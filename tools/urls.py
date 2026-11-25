from django.urls import path
from .views import IndexView, ToolPageView

urlpatterns = [
    path('', IndexView.as_view(), name='home'),
    path('tools/', IndexView.as_view(), name='tools'),
    path('tools/<str:tool_id>/', ToolPageView.as_view(), name='tool-page'),
]
