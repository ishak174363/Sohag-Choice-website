from django.urls import path
from .api_views import (
    ToolsListView, ToolDetailView,
    VaccineScheduleView,
    MilestoneView,
    GrowthCheckView,
    BabyFoodView,
    NamesView,
    FoodCaloriesView,
    DietPlanView,
    PregnancyView,
    HoneyGuideView,
    SupplementView,
    RamadanView,
    HabitListView, HabitToggleView, HabitProgressView,
    BMIView,
    WaterView,
    BooksView,
    BPAnalyzeView,
    DiabetesAnalyzeView,
    LipidAnalyzeView,
    EmergencyGuideView,
    MedicineFAQView,
    TelemedicineConsultationView,
)

urlpatterns = [
    # ── Medicine & Chronic Care ──────────────────────────────
    path('bp/',                       BPAnalyzeView.as_view(),       name='api-bp'),
    path('diabetes/',                 DiabetesAnalyzeView.as_view(), name='api-diabetes'),
    path('lipid/',                    LipidAnalyzeView.as_view(),    name='api-lipid'),
    path('emergency/',                EmergencyGuideView.as_view(),  name='api-emergency'),
    path('medicine-faq/',             MedicineFAQView.as_view(),     name='api-medicine-faq'),
    path('telemedicine/',             TelemedicineConsultationView.as_view(), name='api-telemedicine'),

    # ── Tools Catalog ────────────────────────────────────────
    path('tools/',                    ToolsListView.as_view(),     name='api-tools-list'),
    path('tools/<str:tool_id>/',      ToolDetailView.as_view(),    name='api-tool-detail'),

    # ── Kids Tools ───────────────────────────────────────────
    path('vaccine/',                  VaccineScheduleView.as_view(), name='api-vaccine'),
    path('milestones/',               MilestoneView.as_view(),       name='api-milestones'),
    path('growth/',                   GrowthCheckView.as_view(),     name='api-growth'),
    path('babyfood/',                 BabyFoodView.as_view(),        name='api-babyfood'),
    path('names/',                    NamesView.as_view(),           name='api-names'),
    path('books/',                    BooksView.as_view(),           name='api-books'),

    # ── Food & Nutrition ─────────────────────────────────────
    path('calories/',                 FoodCaloriesView.as_view(),    name='api-calories'),
    path('diet/',                     DietPlanView.as_view(),        name='api-diet'),
    path('honey/',                    HoneyGuideView.as_view(),      name='api-honey'),
    path('supplement/',               SupplementView.as_view(),      name='api-supplement'),
    path('ramadan/',                  RamadanView.as_view(),         name='api-ramadan'),

    # ── Mom ──────────────────────────────────────────────────
    path('pregnancy/',                PregnancyView.as_view(),       name='api-pregnancy'),

    # ── Life / Habit ─────────────────────────────────────────
    path('habit/',                    HabitListView.as_view(),       name='api-habit-list'),
    path('habit/toggle/',             HabitToggleView.as_view(),     name='api-habit-toggle'),
    path('habit/progress/',           HabitProgressView.as_view(),   name='api-habit-progress'),

    # ── Bonus Tools ──────────────────────────────────────────
    path('bmi/',                      BMIView.as_view(),             name='api-bmi'),
    path('water/',                    WaterView.as_view(),           name='api-water'),
]
