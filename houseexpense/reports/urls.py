from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.ReportsHomeView.as_view(), name='reports_home'),
    path('house/<int:house_id>/categories/', views.ExpenseCategoryReportView.as_view(), name='category_report'),
    path('house/<int:house_id>/annual/', views.AnnualReportView.as_view(), name='annual_report'),
    path('house/<int:house_id>/flat-wise/', views.FlatWiseReportView.as_view(), name='flat_wise_report'),
    path('house/<int:house_id>/month-wise/', views.MonthWiseReportView.as_view(), name='month_wise_report'),
    path('api/chart-data/', views.ChartDataAPIView.as_view(), name='chart_data'),
]
