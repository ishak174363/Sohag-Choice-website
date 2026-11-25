from django.test import TestCase
from . import data as D


class ToolboxViewsTest(TestCase):
    def test_index_page(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'সোহাগ চয়েস')

    def test_all_tool_pages(self):
        for tool in D.TOOLS:
            res = self.client.get(f"/tools/{tool['id']}/")
            self.assertEqual(res.status_code, 200, f"Failed for {tool['id']}")

    def test_unknown_tool_404(self):
        res = self.client.get('/tools/nonexistent-tool/')
        self.assertEqual(res.status_code, 404)


class ToolboxApiTest(TestCase):
    def test_tools_list(self):
        res = self.client.get('/api/tools/')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(len(data['tools']), len(D.TOOLS))

    def test_vaccine_schedule(self):
        res = self.client.post('/api/vaccine/', {'dob': '2026-01-01'}, content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(res.json()['schedule']) > 0)

    def test_milestones(self):
        res = self.client.get('/api/milestones/?months=6')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(res.json()['milestones']) > 0)

    def test_growth(self):
        res = self.client.post('/api/growth/', {
            'weight': 7.9, 'height': 68, 'months': 6, 'gender': 'boy'
        }, content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['weight_status'], 'normal')

    def test_babyfood(self):
        res = self.client.get('/api/babyfood/?months=8')
        self.assertEqual(res.status_code, 200)
        self.assertIn('menu', res.json())

    def test_names(self):
        res = self.client.get('/api/names/?gender=ছেলে')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()['count'] > 0)

    def test_books(self):
        res = self.client.get('/api/books/?age_group=২-৪')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()['count'] > 0)

    def test_calories(self):
        res = self.client.get('/api/calories/?q=ভাত')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()['count'] > 0)

    def test_diet(self):
        res = self.client.post('/api/diet/', {
            'weight': 65, 'height': 170, 'age': 28,
            'gender': 'male', 'activity': 'moderate', 'goal': 'maintain'
        }, content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertIn('tdee', res.json())

    def test_pregnancy(self):
        res = self.client.post('/api/pregnancy/', {'lmp': '2026-08-01'}, content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertIn('due_date', res.json())

    def test_honey(self):
        res = self.client.get('/api/honey/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('honey_tests', res.json())

    def test_supplement(self):
        res = self.client.post('/api/supplement/', {
            'answers': {'q1': True, 'q2': True, 'q3': True, 'q8': True}
        }, content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(res.json()['results']) > 0)

    def test_ramadan(self):
        res = self.client.get('/api/ramadan/?district=ঢাকা')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['district'], 'ঢাকা')

    def test_habit_toggle_and_progress(self):
        res = self.client.post('/api/habit/toggle/', {
            'habit_id': 'water', 'habit_name': 'পানি', 'day': 1
        }, content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()['done'])

        prog = self.client.get('/api/habit/progress/?habit_id=water')
        self.assertEqual(prog.status_code, 200)
        self.assertEqual(prog.json()['done'], 1)

    def test_bmi_and_water(self):
        bmi = self.client.post('/api/bmi/', {'weight': 70, 'height': 175}, content_type='application/json')
        self.assertEqual(bmi.status_code, 200)
        self.assertIn('bmi', bmi.json())

        water = self.client.post('/api/water/', {'weight': 70, 'age': 28, 'active': True}, content_type='application/json')
        self.assertEqual(water.status_code, 200)
        self.assertIn('glasses', water.json())

    def test_bp_analysis(self):
        res = self.client.post('/api/bp/', {'systolic': 118, 'diastolic': 76}, content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertIn('stage', res.json())
        self.assertEqual(res.json()['stage']['id'], 'normal')

        # Crisis test
        res_crisis = self.client.post('/api/bp/', {'systolic': 190, 'diastolic': 125}, content_type='application/json')
        self.assertEqual(res_crisis.status_code, 200)
        self.assertTrue(res_crisis.json()['emergency_alert'])

    def test_diabetes_analysis(self):
        # Fasting normal
        res = self.client.post('/api/diabetes/', {'test_type': 'fasting', 'value': 5.2, 'unit': 'mmol'}, content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertIn('category', res.json())

        # Hypoglycemia test (<3.9)
        res_hypo = self.client.post('/api/diabetes/', {'test_type': 'fasting', 'value': 3.2, 'unit': 'mmol'}, content_type='application/json')
        self.assertEqual(res_hypo.status_code, 200)
        self.assertTrue(res_hypo.json()['is_hypo'])
        self.assertIsNotNone(res_hypo.json()['hypo_rule'])

    def test_lipid_analysis(self):
        res = self.client.post('/api/lipid/', {
            'total': 210, 'ldl': 130, 'hdl': 45, 'tg': 170
        }, content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertIn('cholesterol_ratio', res.json())
        self.assertTrue(len(res.json()['evaluations']) == 4)

    def test_emergency_and_faqs(self):
        emg = self.client.get('/api/emergency/')
        self.assertEqual(emg.status_code, 200)
        self.assertTrue(len(emg.json()['emergencies']) >= 4)

        faq = self.client.get('/api/medicine-faq/?q=sugar')
        self.assertEqual(faq.status_code, 200)
        self.assertIn('faqs', faq.json())

    def test_telemedicine_booking(self):
        # GET doctor info
        get_res = self.client.get('/api/telemedicine/')
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()['doctor']['phone'], '01625946298')

        # POST consultation booking
        post_res = self.client.post('/api/telemedicine/', {
            'name': 'কামরুল হাসান',
            'phone': '01712345678',
            'age': '45',
            'gender': 'পুরুষ',
            'preferred_time': 'আজ রাত ৮:০০ — ৯:০০',
            'chief_complaint': 'প্রেশার ওঠানামা করছে এবং মাথা ঘোরে।'
        }, content_type='application/json')
        self.assertEqual(post_res.status_code, 201)
        self.assertTrue(post_res.json()['success'])
        self.assertIn('8801785949700', post_res.json()['wa_url'])
