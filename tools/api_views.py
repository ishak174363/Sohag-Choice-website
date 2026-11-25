"""
Sohag Health Toolbox – API Views (Class-Based, DRF APIView)
All endpoints return JSON. Each resource has its own class.
"""
from datetime import date, timedelta
import calendar

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from . import data as D
from .models import HabitEntry, TelemedicineConsultation
from .serializers import TelemedicineConsultationSerializer


# ═══════════════════════════════════════════════════════════════
#  Shared Helpers
# ═══════════════════════════════════════════════════════════════

class _DateHelper:
    @staticmethod
    def add_days(d: date, n: int) -> date:
        return d + timedelta(days=n)

    @staticmethod
    def add_months(d: date, n: int) -> date:
        month = d.month - 1 + n
        year  = d.year + month // 12
        month = month % 12 + 1
        day   = min(d.day, calendar.monthrange(year, month)[1])
        return date(year, month, day)


WHO_WEIGHT_BOYS = {
    0:  (2.5, 3.3, 4.4), 1:  (3.4, 4.3, 5.7), 2:  (4.3, 5.4, 7.0),
    3:  (5.0, 6.2, 8.0), 4:  (5.6, 6.9, 8.9), 5:  (6.1, 7.5, 9.6),
    6:  (6.4, 7.9, 10.1), 9:  (7.2, 8.9, 11.4), 12: (7.7, 9.6, 12.4),
    18: (8.1, 10.2, 13.2), 24: (9.0, 11.3, 14.4), 36: (10.8, 13.4, 17.3),
    48: (12.0, 14.9, 19.8), 60: (13.0, 16.4, 21.6),
}
WHO_WEIGHT_GIRLS = {
    0:  (2.4, 3.2, 4.2), 1:  (3.2, 4.0, 5.2), 2:  (4.0, 5.1, 6.6),
    3:  (4.6, 5.8, 7.5), 4:  (5.1, 6.4, 8.2), 5:  (5.5, 6.9, 8.8),
    6:  (5.7, 7.3, 9.3), 9:  (6.5, 8.2, 10.6), 12: (7.0, 8.9, 11.5),
    18: (7.8, 9.9, 12.9), 24: (8.7, 11.0, 14.3), 36: (10.2, 13.0, 16.8),
    48: (11.5, 14.6, 19.5), 60: (12.7, 16.2, 21.4),
}

def _who_lookup(table: dict, months: int) -> tuple:
    for key in sorted(table.keys(), reverse=True):
        if months >= key:
            return table[key]
    return table[min(table.keys())]


# ═══════════════════════════════════════════════════════════════
#  Tools Catalog
# ═══════════════════════════════════════════════════════════════

class ToolsListView(APIView):
    """GET /api/tools/ — full tools catalog with group metadata."""

    def get(self, request):
        group_map = {g['id']: g for g in D.GROUPS}
        tools = [
            {
                'id':         t['id'],
                'name':       t['name'],
                'short':      t['short'],
                'icon':       t['icon'],
                'group':      t['group'],
                'group_name': group_map.get(t['group'], {}).get('name', ''),
                'color':      group_map.get(t['group'], {}).get('color', '#34D37B'),
                'bg':         group_map.get(t['group'], {}).get('bg', '#EAF6C4'),
            }
            for t in D.TOOLS
        ]
        return Response({'tools': tools, 'groups': D.GROUPS})


class ToolDetailView(APIView):
    """GET /api/tools/<tool_id>/ — single tool metadata."""

    def get(self, request, tool_id):
        tool = next((t for t in D.TOOLS if t['id'] == tool_id), None)
        if not tool:
            return Response(
                {'error': 'Tool not found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        group_map = {g['id']: g for g in D.GROUPS}
        g = group_map.get(tool['group'], {})
        return Response({
            **tool,
            'group_name': g.get('name', ''),
            'color':      g.get('color', ''),
            'bg':         g.get('bg', ''),
        })


# ═══════════════════════════════════════════════════════════════
#  Vaccine Schedule
# ═══════════════════════════════════════════════════════════════

class VaccineScheduleView(APIView):
    """
    POST /api/vaccine/
    Body: { "dob": "YYYY-MM-DD" }
    Returns full EPI schedule with per-visit status.
    """

    def post(self, request):
        dob_str = request.data.get('dob', '')
        try:
            dob = date.fromisoformat(dob_str)
        except (ValueError, TypeError):
            return Response(
                {'error': 'জন্মতারিখ দিন (YYYY-MM-DD ফরম্যাটে)'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        today    = date.today()
        schedule = []

        for v in D.VACCINES:
            if 'days_after_birth' in v:
                vdate = _DateHelper.add_days(dob, v['days_after_birth'])
            else:
                vdate = _DateHelper.add_months(dob, v['months_after_birth'])

            diff = (vdate - today).days
            if diff > 0:
                vac_status = 'upcoming'
            elif diff == 0:
                vac_status = 'today'
            elif diff >= -14:
                vac_status = 'recent'
            else:
                vac_status = 'overdue'

            schedule.append({
                'when':   v['when'],
                'date':   vdate.isoformat(),
                'days':   diff,
                'status': vac_status,
                'items':  v['items'],
            })

        return Response({'dob': dob_str, 'schedule': schedule})


# ═══════════════════════════════════════════════════════════════
#  Milestone Checklist
# ═══════════════════════════════════════════════════════════════

class MilestoneView(APIView):
    """
    GET /api/milestones/?months=<float>
    Returns age-appropriate milestones (or all if no filter).
    """

    def get(self, request):
        months_param = request.query_params.get('months')

        if months_param is None:
            return Response({'milestones': D.MILESTONES})

        try:
            m = float(months_param)
        except ValueError:
            return Response(
                {'error': 'months মান সঠিক দিন'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        filtered = [
            ms for ms in D.MILESTONES
            if ms['min_months'] <= m < ms['max_months']
        ]
        return Response({
            'milestones': filtered or D.MILESTONES,
            'filtered':   bool(filtered),
            'months':     m,
        })


# ═══════════════════════════════════════════════════════════════
#  Growth Chart (WHO)
# ═══════════════════════════════════════════════════════════════

class GrowthCheckView(APIView):
    """
    POST /api/growth/
    Body: { "weight": float, "height": float, "months": int, "gender": "boy"|"girl" }
    """

    def post(self, request):
        try:
            weight = float(request.data.get('weight', 0))
            height = float(request.data.get('height', 0))
            months = int(request.data.get('months', 0))
            gender = request.data.get('gender', 'boy')
        except (ValueError, TypeError):
            return Response(
                {'error': 'ওজন, উচ্চতা ও বয়স সঠিকভাবে দিন'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        table        = WHO_WEIGHT_BOYS if gender == 'boy' else WHO_WEIGHT_GIRLS
        low, mid, hi = _who_lookup(table, months)

        if weight < low:
            w_status, w_label = 'low',    'ওজন কম ⚠️'
        elif weight > hi:
            w_status, w_label = 'high',   'ওজন বেশি ⚠️'
        else:
            w_status, w_label = 'normal', 'স্বাভাবিক ✓'

        bmi = round(weight / ((height / 100) ** 2), 1) if height > 0 else None

        return Response({
            'weight':        weight,
            'height':        height,
            'months':        months,
            'gender':        gender,
            'who_range':     {'low': low, 'median': mid, 'high': hi},
            'weight_status': w_status,
            'weight_label':  w_label,
            'bmi':           bmi,
            'advice':        'ডাক্তারের সাথে চার্ট নিয়ে আলোচনা করুন।',
        })


# ═══════════════════════════════════════════════════════════════
#  Baby Food Menu
# ═══════════════════════════════════════════════════════════════

class BabyFoodView(APIView):
    """GET /api/babyfood/?months=<float>"""

    def get(self, request):
        try:
            m = float(request.query_params.get('months', 6))
        except ValueError:
            m = 6.0

        menu = next(
            (bm for bm in D.BABY_FOOD_MENUS if bm['min_months'] <= m < bm['max_months']),
            D.BABY_FOOD_MENUS[-1],
        )
        return Response({'months': m, 'menu': menu})


# ═══════════════════════════════════════════════════════════════
#  Baby Names
# ═══════════════════════════════════════════════════════════════

class NamesView(APIView):
    """
    GET /api/names/?gender=ছেলে|মেয়ে&type=ইসলামিক|বাংলা&q=<search>
    """

    def get(self, request):
        gender    = request.query_params.get('gender', '')
        name_type = request.query_params.get('type', '')
        query     = request.query_params.get('q', '').lower()

        names = D.BABY_NAMES
        if gender:
            names = [n for n in names if n['gender'] == gender]
        if name_type:
            names = [n for n in names if n['type'] == name_type]
        if query:
            names = [
                n for n in names
                if query in n['name'].lower()
                or query in n['english'].lower()
                or query in n['meaning'].lower()
            ]

        return Response({'names': names, 'count': len(names)})


# ═══════════════════════════════════════════════════════════════
#  Food Calories
# ═══════════════════════════════════════════════════════════════

class FoodCaloriesView(APIView):
    """GET /api/calories/?q=<search>&category=<cat>"""

    def get(self, request):
        query    = request.query_params.get('q', '').lower()
        category = request.query_params.get('category', '')

        foods = D.FOOD_CALORIES
        if query:
            foods = [f for f in foods if query in f['name'].lower()]
        if category:
            foods = [f for f in foods if f['category'] == category]

        categories = sorted({f['category'] for f in D.FOOD_CALORIES})
        return Response({'foods': foods, 'categories': categories, 'count': len(foods)})


# ═══════════════════════════════════════════════════════════════
#  Diet Plan (BMR / TDEE)
# ═══════════════════════════════════════════════════════════════

class DietPlanView(APIView):
    """
    POST /api/diet/
    Body: { weight, height, age, gender, activity, goal }
    """

    ACTIVITY_FACTORS = {
        'sedentary':  1.2,
        'light':      1.375,
        'moderate':   1.55,
        'active':     1.725,
        'very_active':1.9,
    }

    def post(self, request):
        try:
            weight   = float(request.data.get('weight', 0))
            height   = float(request.data.get('height', 0))
            age      = int(request.data.get('age', 25))
            gender   = request.data.get('gender', 'female')
            activity = request.data.get('activity', 'moderate')
            goal     = request.data.get('goal', 'maintain')
        except (ValueError, TypeError):
            return Response(
                {'error': 'সঠিক তথ্য দিন'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Mifflin-St Jeor equation
        bmr = (10 * weight + 6.25 * height - 5 * age
               + (5 if gender == 'male' else -161))

        tdee = bmr * self.ACTIVITY_FACTORS.get(activity, 1.55)

        goal_map = {
            'lose':     (tdee - 500, 'ওজন কমানো (প্রতি সপ্তাহে ~০.৫ কেজি)'),
            'gain':     (tdee + 400, 'ওজন বাড়ানো (প্রতি সপ্তাহে ~০.৪ কেজি)'),
            'maintain': (tdee,       'ওজন ধরে রাখা'),
        }
        target, goal_label = goal_map.get(goal, goal_map['maintain'])

        bmi = round(weight / ((height / 100) ** 2), 1)
        bmi_label = (
            'কম ওজন'    if bmi < 18.5 else
            'স্বাভাবিক' if bmi < 25   else
            'বেশি ওজন'  if bmi < 30   else
            'স্থূলতা'
        )

        return Response({
            'bmr':        round(bmr),
            'tdee':       round(tdee),
            'target':     round(target),
            'bmi':        bmi,
            'bmi_label':  bmi_label,
            'goal_label': goal_label,
            'macros': {
                'protein_g': round(weight * 1.6),
                'fat_g':     round(target * 0.25 / 9),
                'carb_g':    round((target - weight * 1.6 * 4 - target * 0.25) / 4),
            },
            'tips': [
                'প্রতি বেলায় থালার অর্ধেক রাখুন সবজি ও ফল',
                'সাদা ভাতের বদলে লাল চালের ভাত খান',
                'ভাজাপোড়া কমিয়ে সেদ্ধ বা গ্রিল করুন',
                'খাওয়ার আগে এক গ্লাস পানি পান করুন',
            ],
        })


# ═══════════════════════════════════════════════════════════════
#  Pregnancy Week Tracker
# ═══════════════════════════════════════════════════════════════

class PregnancyView(APIView):
    """
    POST /api/pregnancy/
    Body: { "lmp": "YYYY-MM-DD" }  (Last Menstrual Period)
    """

    def post(self, request):
        lmp_str = request.data.get('lmp', '')
        try:
            lmp = date.fromisoformat(lmp_str)
        except (ValueError, TypeError):
            return Response(
                {'error': 'শেষ মাসিকের তারিখ দিন (YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        today     = date.today()
        total_days= (today - lmp).days
        week      = total_days // 7
        due       = lmp + timedelta(days=280)

        # find best matching week info
        info = D.PREGNANCY_WEEKS[0]
        for pw in D.PREGNANCY_WEEKS:
            if week >= pw['week']:
                info = pw

        trimester = 1 if week <= 12 else (2 if week <= 27 else 3)

        return Response({
            'lmp':        lmp_str,
            'week':       week,
            'days':       total_days % 7,
            'due_date':   due.isoformat(),
            'trimester':  trimester,
            'weeks_left': max(0, 40 - week),
            'info':       info,
        })


# ═══════════════════════════════════════════════════════════════
#  Honey & Ghee Guide
# ═══════════════════════════════════════════════════════════════

class HoneyGuideView(APIView):
    """GET /api/honey/ — adulteration tests & tips."""

    _DATA = {
        'intro': 'বাজারে অনেক ভেজাল মধু ও ঘি পাওয়া যায়। নিচের পরীক্ষাগুলো বাড়িতেই করা যায়।',
        'honey_tests': [
            {
                'name': 'পানি পরীক্ষা',
                'method': 'এক চামচ মধু এক গ্লাস পানিতে ফেলুন।',
                'real': 'খাঁটি মধু তলায় থাকে, ছড়ায় না।',
                'fake': 'ভেজাল মধু পানিতে মিশে যায়।',
                'reliable': True,
            },
            {
                'name': 'বুড়ো আঙুল পরীক্ষা',
                'method': 'বুড়ো আঙুলে মধু লাগান।',
                'real': 'ছড়ায় না, এক জায়গায় থাকে।',
                'fake': 'পানির মতো ছড়িয়ে যায়।',
                'reliable': True,
            },
            {
                'name': 'পিঁপড়া পরীক্ষা',
                'method': 'মধু পিঁপড়ার কাছে রাখুন।',
                'real': 'পিঁপড়া সাধারণত খায় না।',
                'fake': 'পিঁপড়া দ্রুত ভিড় করে।',
                'reliable': False,
                'note': 'এটি নির্ভরযোগ্য নয় – পিঁপড়া খাঁটি মধুও খায়।',
            },
        ],
        'ghee_tests': [
            {
                'name': 'গলন পরীক্ষা',
                'method': 'হাতের তালুতে সামান্য ঘি নিন।',
                'real': 'শরীরের তাপেই গলে যায়।',
                'fake': 'গলতে সময় লাগে।',
                'reliable': True,
            },
            {
                'name': 'ফ্রিজ পরীক্ষা',
                'method': 'ফ্রিজে রাখুন কিছুক্ষণ।',
                'real': 'পুরোটা একসাথে জমে, আলাদা স্তর নেই।',
                'fake': 'আলাদা স্তরে জমে।',
                'reliable': True,
            },
        ],
        'tips': [
            'বিশ্বস্ত বিক্রেতা বা পরিচিত খামার থেকে কিনুন।',
            'সিজনাল মধুতে স্বাদ ও রঙ ভিন্ন হয়, এটা স্বাভাবিক।',
            'ক্রিস্টালাইজড (জমে যাওয়া) মধু খাঁটি হওয়ার লক্ষণ।',
            'ল্যাবে পরীক্ষাই একমাত্র নিশ্চিত উপায়।',
        ],
    }

    def get(self, request):
        return Response(self._DATA)


# ═══════════════════════════════════════════════════════════════
#  Supplement Quiz
# ═══════════════════════════════════════════════════════════════

class SupplementView(APIView):
    """
    GET  /api/supplement/        → quiz questions
    POST /api/supplement/        → { "answers": {"q1": true, "q3": true, ...} }
    """

    def get(self, request):
        return Response({'questions': D.SUPPLEMENT_QUESTIONS})

    def post(self, request):
        answers = request.data.get('answers', {})
        scores  = {}

        for q in D.SUPPLEMENT_QUESTIONS:
            if answers.get(q['id'], False):
                for s in q['suggests']:
                    scores[s] = scores.get(s, 0) + 1

        results = [
            {'key': key, 'score': count, **D.SUPPLEMENT_INFO[key]}
            for key, count in sorted(scores.items(), key=lambda x: -x[1])
            if count >= 2 and key in D.SUPPLEMENT_INFO
        ]

        return Response({
            'results':    results,
            'disclaimer': 'এটি সাধারণ তথ্য মাত্র। সাপ্লিমেন্ট শুরু করার আগে ডাক্তারের পরামর্শ নিন।',
        })


# ═══════════════════════════════════════════════════════════════
#  Ramadan Times
# ═══════════════════════════════════════════════════════════════

class RamadanView(APIView):
    """GET /api/ramadan/?district=ঢাকা"""

    def get(self, request):
        district = request.query_params.get('district', 'ঢাকা')
        return Response({
            'district':      district,
            'districts':     D.RAMADAN_DISTRICTS,
            'note':          'সঠিক সেহরি-ইফতারের সময় ইসলামিক ফাউন্ডেশনের সময়সূচি (islamicfoundation.gov.bd) দেখুন।',
            'iftar_tips':    D.RAMADAN_TIPS,
            'healthy_iftar': [
                '🌴 খেজুর ৩টি (সুন্নাহ ও দ্রুত শক্তি)',
                '💧 পানি ২ গ্লাস (ডিহাইড্রেশন ঠেকাতে)',
                '🍲 হালকা স্যুপ (পেট গরম করতে)',
                '🍚 ভাত-তরকারি (মূল খাবার)',
                '🍌 ফল (ভিটামিন ও ফাইবার)',
            ],
            'healthy_sehri': [
                '🍚 লাল চালের ভাত বা রুটি (ধীরে শক্তি দেয়)',
                '🥚 ডিম (প্রোটিন)',
                '🥛 দুধ বা দই (ক্যালসিয়াম ও তৃষ্ণা কমায়)',
                '🥦 সবজি (ভিটামিন)',
                '💧 প্রচুর পানি',
            ],
        })


# ═══════════════════════════════════════════════════════════════
#  Habit Challenge
# ═══════════════════════════════════════════════════════════════

class HabitListView(APIView):
    """GET /api/habit/ — all habit ideas."""

    def get(self, request):
        return Response({'habits': D.HABIT_IDEAS})


class HabitToggleView(APIView):
    """
    POST /api/habit/toggle/
    Body: { habit_id, habit_name, day }
    Requires session (uses session_key for anonymous tracking).
    """

    def post(self, request):
        if not request.session.session_key:
            request.session.create()

        session_key = request.session.session_key
        habit_id    = request.data.get('habit_id')
        day         = request.data.get('day')
        habit_name  = request.data.get('habit_name', '')

        if not habit_id or day is None:
            return Response(
                {'error': 'habit_id ও day দিন'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        entry, _ = HabitEntry.objects.get_or_create(
            session_key=session_key,
            habit_id=habit_id,
            day=int(day),
            defaults={'habit_name': habit_name, 'done': False},
        )
        entry.done = not entry.done
        entry.save()

        return Response({'habit_id': habit_id, 'day': day, 'done': entry.done})


class HabitProgressView(APIView):
    """GET /api/habit/progress/?habit_id=<id>"""

    def get(self, request):
        if not request.session.session_key:
            request.session.create()

        session_key = request.session.session_key
        habit_id    = request.query_params.get('habit_id')

        qs = HabitEntry.objects.filter(session_key=session_key)
        if habit_id:
            qs = qs.filter(habit_id=habit_id)

        done_days = list(qs.filter(done=True).values('habit_id', 'day'))
        total     = qs.count()
        done      = qs.filter(done=True).count()

        return Response({
            'done_days': done_days,
            'total':     total,
            'done':      done,
            'percent':   round(done / 30 * 100) if habit_id else 0,
        })


# ═══════════════════════════════════════════════════════════════
#  BMI Calculator (Bonus)
# ═══════════════════════════════════════════════════════════════

class BMIView(APIView):
    """
    POST /api/bmi/
    Body: { "weight": float, "height": float }
    """

    def post(self, request):
        try:
            weight = float(request.data.get('weight', 0))
            height = float(request.data.get('height', 0))
        except (ValueError, TypeError):
            return Response(
                {'error': 'সঠিক ওজন ও উচ্চতা দিন'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if height <= 0:
            return Response(
                {'error': 'উচ্চতা দিন (সেন্টিমিটারে)'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        bmi = round(weight / ((height / 100) ** 2), 1)

        if bmi < 18.5:
            label, color = 'কম ওজন',    '#3D6FB0'
        elif bmi < 25:
            label, color = 'স্বাভাবিক ✓','#34D37B'
        elif bmi < 30:
            label, color = 'বেশি ওজন',  '#FCD34D'
        else:
            label, color = 'স্থূলতা',   '#FB7185'

        ideal_low  = round(18.5 * (height / 100) ** 2, 1)
        ideal_high = round(24.9 * (height / 100) ** 2, 1)

        return Response({
            'weight':       weight,
            'height':       height,
            'bmi':          bmi,
            'label':        label,
            'color':        color,
            'ideal_range':  f'{ideal_low}–{ideal_high} কেজি',
            'advice':       'বিএমআই একটি আনুমানিক সূচক। ডাক্তারের পরামর্শ নিন।',
        })


# ═══════════════════════════════════════════════════════════════
#  Daily Water Intake (Bonus)
# ═══════════════════════════════════════════════════════════════

class WaterView(APIView):
    """
    POST /api/water/
    Body: { "weight": float, "age": int, "active": bool }
    """

    def post(self, request):
        try:
            weight = float(request.data.get('weight', 60))
            age    = int(request.data.get('age', 25))
            active = bool(request.data.get('active', False))
        except (ValueError, TypeError):
            return Response(
                {'error': 'সঠিক তথ্য দিন'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        base_ml = weight * 35
        if active:
            base_ml += 500
        if age > 55:
            base_ml -= 200

        glasses = round(base_ml / 250)

        return Response({
            'weight':  weight,
            'ml':      round(base_ml),
            'glasses': glasses,
            'liters':  round(base_ml / 1000, 1),
            'tips': [
                'সকালে উঠে ১ গ্লাস পানি পান করুন।',
                'প্রতি খাবারের আগে ১ গ্লাস পানি পান করুন।',
                'প্রস্রাবের রঙ হালকা হলুদ হওয়া উচিত।',
                'গরম বা ব্যায়ামের সময় বেশি পানি নিন।',
            ],
        })


# ═══════════════════════════════════════════════════════════════
#  Children's Books Finder
# ═══════════════════════════════════════════════════════════════

class BooksView(APIView):
    """GET /api/books/?age_group=২-৪&interest=গল্প"""

    def get(self, request):
        age_group = request.query_params.get('age_group', '')
        interest  = request.query_params.get('interest', '')

        books = D.BOOKS
        if age_group:
            books = [b for b in books if b['age_group'] == age_group]
        if interest:
            books = [b for b in books if b['interest'] == interest]

        age_groups = ['০-১', '১-২', '২-৪', '৪-৬', '৬+']
        interests  = sorted({b['interest'] for b in D.BOOKS})
        return Response({
            'books':      books,
            'count':      len(books),
            'age_groups': age_groups,
            'interests':  interests,
        })


# ═══════════════════════════════════════════════════════════════
#  Medicine & Chronic Care Endpoints (AHA & DGHS Guidelines)
# ═══════════════════════════════════════════════════════════════

class BPAnalyzeView(APIView):
    """
    POST /api/bp/
    Body: { systolic: 135, diastolic: 85 }
    Returns clinical categorization, MAP, pulse pressure, lifestyle plan.
    """

    def post(self, request):
        try:
            sys = int(request.data.get('systolic', 0))
            dia = int(request.data.get('diastolic', 0))
        except (ValueError, TypeError):
            return Response({'error': 'সঠিক সিস্টোলিক ও ডায়াস্টোলিক সংখ্যা দিন'}, status=status.HTTP_400_BAD_REQUEST)

        if sys <= 50 or dia <= 30 or sys > 260 or dia > 180:
            return Response({'error': 'রক্তচাপের মান যৌক্তিক পরিসীমায় দিন (যেমন: ১২০ ও ৮০)'}, status=status.HTTP_400_BAD_REQUEST)

        # Categorization based on AHA/ACC & DGHS guidelines
        if sys > 180 or dia > 120:
            stage_id = 'crisis'
        elif sys >= 140 or dia >= 90:
            stage_id = 'stage2'
        elif (130 <= sys <= 139) or (80 <= dia <= 89):
            stage_id = 'stage1'
        elif (120 <= sys <= 129) and dia < 80:
            stage_id = 'elevated'
        else:
            stage_id = 'normal'

        stage = next(s for s in D.BP_STAGES if s['id'] == stage_id)
        pulse_pressure = sys - dia
        map_val = round((2 * dia + sys) / 3, 1)

        return Response({
            'systolic': sys,
            'diastolic': dia,
            'stage': stage,
            'pulse_pressure': pulse_pressure,
            'map': map_val,
            'all_stages': D.BP_STAGES,
            'emergency_alert': stage_id == 'crisis',
            'dash_tips': [
                'খাবারে কাঁচা লবণ ও প্রক্রিয়াজাত লবণাক্ত খাবার সম্পূর্ণ বর্জন করুন (দৈনিক < ৫ গ্রাম)।',
                'পটাশিয়াম সমৃদ্ধ ফলমূল (কলা, ডাবের পানি, বেদানা) ও তাজা শাকসবজি বেশি খান।',
                'প্রতিদিন অন্তত ৩০ মিনিট দ্রুত গতিতে হাঁটুন (সপ্তাহে ১৫০ মিনিট)।',
                'ধূমপান ও জর্দা সম্পূর্ণ পরিহার করুন এবং পর্যাপ্ত ঘুমান (৭-৮ ঘণ্টা)।',
            ]
        })


class DiabetesAnalyzeView(APIView):
    """
    POST /api/diabetes/
    Body: { test_type: 'fasting'|'post_meal'|'hba1c'|'random', value: 7.2, unit: 'mmol'|'mgdl' }
    """

    def post(self, request):
        test_type = request.data.get('test_type', 'fasting')
        unit = request.data.get('unit', 'mmol')
        try:
            val = float(request.data.get('value', 0))
        except (ValueError, TypeError):
            return Response({'error': 'রক্তের সুগারের সঠিক মান দিন'}, status=status.HTTP_400_BAD_REQUEST)

        # Convert mg/dL to mmol/L for standardized evaluation
        mmol_val = val
        if unit == 'mgdl' and test_type != 'hba1c':
            mmol_val = round(val / 18.0, 1)

        is_hypo = False
        hypo_alert = None
        if test_type != 'hba1c' and mmol_val < 3.9:
            is_hypo = True
            hypo_alert = D.DIABETES_DATA['rule_of_15']

        # Evaluation
        if test_type == 'hba1c':
            if val < 5.7:
                category = 'স্বাভাবিক (Normal)'
                color = '#0E7A47'
                assessment = 'আপনার ৩ মাসের গড় রক্তে সুগার চমৎকার নিয়ন্ত্রণে রয়েছে।'
            elif val <= 6.4:
                category = 'প্রি-ডায়াবেটিস (Prediabetes)'
                color = '#D97706'
                assessment = 'ডায়াবেটিসের প্রাথমিক ঝুঁকি রয়েছে। এখনই খাবার ও হাঁটার অভ্যাসে সতর্ক হোন।'
            else:
                category = 'ডায়াবেটিস (Diabetes)'
                color = '#DC2626'
                assessment = 'রক্তের সুগার অনিয়ন্ত্রিত। ডায়াবেটোলজিস্টের পরামর্শে ওষুধ ও ইনসুলিন সমন্বয় জরুরি।'
        elif test_type == 'fasting':
            if mmol_val < 5.6:
                category = 'স্বাভাবিক (Normal)'
                color = '#0E7A47'
                assessment = 'খালি পেটে আপনার রক্তে সুগার স্বাভাবিক পরিসীমায় রয়েছে।'
            elif mmol_val <= 6.9:
                category = 'ইমপেয়ার্ড ফাস্টিং গ্লুকোজ (প্রি-ডায়াবেটিস)'
                color = '#D97706'
                assessment = 'ফাস্টিং সুগার সামান্য বেশি। ওজন কমানো ও লাইফস্টাইল পরিবর্তন আবশ্যক।'
            else:
                category = 'ডায়াবেটিস (Diabetes)'
                color = '#DC2626'
                assessment = 'ফাস্টিং সুগার ৭.০ বা বেশি। এটি নিশ্চিত ডায়াবেটিসের নির্দেশক।'
        else:  # post_meal or random
            if mmol_val < 7.8:
                category = 'স্বাভাবিক (Normal)'
                color = '#0E7A47'
                assessment = 'খাবারের পর সুগার স্বাভাবিক পরিসীমায় রয়েছে।'
            elif mmol_val <= 11.0:
                category = 'ইমপেয়ার্ড গ্লুকোজ টলারেন্স (প্রি-ডায়াবেটিস)'
                color = '#D97706'
                assessment = 'খাবার পর সুগার বেশি উঠছে। মিষ্টি, কোমল পানীয় ও অতিরিক্ত ভাত বর্জন করুন।'
            else:
                category = 'ডায়াবেটিস (Diabetes)'
                color = '#DC2626'
                assessment = 'খাবার পর সুগার ১১.১ বা তার বেশি। ডাক্তারের পরামর্শে সঠিক চিকিৎসা শুরু করুন।'

        return Response({
            'test_type': test_type,
            'input_value': val,
            'unit': unit,
            'mmol_value': mmol_val,
            'category': category,
            'color': color,
            'assessment': assessment,
            'is_hypo': is_hypo,
            'hypo_rule': hypo_alert,
            'criteria': D.DIABETES_DATA['criteria'],
            'lifestyle_rules': D.DIABETES_DATA['lifestyle_rules']
        })


class LipidAnalyzeView(APIView):
    """
    POST /api/lipid/
    Body: { total: 210, ldl: 135, hdl: 42, tg: 180 }
    """

    def post(self, request):
        try:
            total = float(request.data.get('total', 0))
            ldl = float(request.data.get('ldl', 0))
            hdl = float(request.data.get('hdl', 0))
            tg = float(request.data.get('tg', 0))
        except (ValueError, TypeError):
            return Response({'error': 'কোলেস্টেরলের প্রতিটি মান সঠিক সংখ্যায় দিন'}, status=status.HTTP_400_BAD_REQUEST)

        ratio = round(total / hdl, 1) if hdl > 0 else 0
        ratio_status = 'আদর্শ' if ratio < 4.0 else ('মধ্যম ঝুঁকি' if ratio <= 5.0 else 'উচ্চ ঝুঁকি')

        evaluations = [
            {
                'name': 'টোটাল কোলেস্টেরল',
                'value': f"{int(total)} mg/dL",
                'status': 'স্বাভাবিক' if total < 200 else ('বর্ডারলাইন' if total < 240 else 'উচ্চ'),
                'color': '#0E7A47' if total < 200 else ('#D97706' if total < 240 else '#DC2626')
            },
            {
                'name': 'এলডিএল (খারাপ চর্বি)',
                'value': f"{int(ldl)} mg/dL",
                'status': 'আদর্শ' if ldl < 100 else ('বর্ডারলাইন' if ldl < 160 else 'বিপজ্জনক'),
                'color': '#0E7A47' if ldl < 100 else ('#D97706' if ldl < 160 else '#DC2626')
            },
            {
                'name': 'এইচডিএল (ভালো চর্বি)',
                'value': f"{int(hdl)} mg/dL",
                'status': 'সুরক্ষিত' if hdl >= 50 else ('স্বাভাবিক' if hdl >= 40 else 'কম (ঝুঁকিপূর্ণ)'),
                'color': '#0E7A47' if hdl >= 50 else ('#D97706' if hdl >= 40 else '#DC2626')
            },
            {
                'name': 'ট্রাইগ্লিসারাইড',
                'value': f"{int(tg)} mg/dL",
                'status': 'স্বাভাবিক' if tg < 150 else ('বর্ডারলাইন' if tg < 200 else 'উচ্চ'),
                'color': '#0E7A47' if tg < 150 else ('#D97706' if tg < 200 else '#DC2626')
            },
        ]

        return Response({
            'evaluations': evaluations,
            'cholesterol_ratio': ratio,
            'ratio_status': ratio_status,
            'targets': D.LIPID_DATA['targets'],
            'fatty_liver_tips': D.LIPID_DATA['fatty_liver_tips'],
        })


class EmergencyGuideView(APIView):
    """GET /api/emergency/"""

    def get(self, request):
        return Response({
            'emergencies': D.EMERGENCY_DATA,
            'emergency_hotline': '999',
            'doctor_hotline': D.DOCTOR_INFO['phone']
        })


class MedicineFAQView(APIView):
    """GET /api/medicine-faq/?q=sugar"""

    def get(self, request):
        q = request.query_params.get('q', '').strip().lower()
        faqs = D.MEDICINE_FAQ_DATA
        if q:
            faqs = [f for f in faqs if q in f['q'].lower() or q in f['a'].lower()]
        return Response({
            'faqs': faqs,
            'total': len(faqs)
        })


class TelemedicineConsultationView(APIView):
    """
    GET /api/telemedicine/ — Returns doctor info & profile
    POST /api/telemedicine/ — Submits consultation request & builds WhatsApp consultation link
    """

    def get(self, request):
        return Response({
            'doctor': D.DOCTOR_INFO,
        })

    def post(self, request):
        serializer = TelemedicineConsultationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        consultation = serializer.save()

        # Build WhatsApp personalized consultation URL
        wa_text = (
            f"আসসালামু আলাইকুম ডা. সোহাগ স্যার,\n"
            f"আমি আপনার ওয়েবসাইট থেকে সরাসরি যোগাযোগ করছি।\n\n"
            f"👤 রোগীর নাম: {consultation.name}\n"
            f"📞 ফোন: {consultation.phone}\n"
            f"🎂 বয়স/লিঙ্গ: {consultation.age or 'উল্লেখ নেই'} / {consultation.gender or 'উল্লেখ নেই'}\n"
            f"🩺 সমস্যা/লক্ষণ: {consultation.chief_complaint}\n\n"
            f"(রেফারেন্স আইডি: #{consultation.id})"
        )
        import urllib.parse
        wa_url = f"https://wa.me/{D.DOCTOR_INFO['whatsapp']}?text={urllib.parse.quote(wa_text)}"

        return Response({
            'success': True,
            'booking_id': consultation.id,
            'message': 'আপনার তথ্য সফলভাবে সংরক্ষিত হয়েছে। সরাসরি ডা. সোহাগ হাসানের সাথে হোয়াটসঅ্যাপে আলোচনা শুরু করতে নিচের বাটনে ক্লিক করুন।',
            'wa_url': wa_url,
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
