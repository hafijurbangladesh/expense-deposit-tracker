from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('house/<int:house_id>/transactions/', views.HouseExpenseDepositView.as_view(), name='house_transactions'),
    path('house/<int:house_id>/add-deposit/', views.HouseExpenseDepositView.as_view(), name='add_deposit'),
    path('house/<int:house_id>/collect-service-charge/', views.CollectServiceChargeView.as_view(), name='collect_service_charge'),
    path('house/<int:house_id>/add-expenses/', views.AddExpensesView.as_view(), name='add_expenses'),
    path('house/<int:house_id>/monthly-report/', views.MonthlyReportView.as_view(), name='monthly_report'),
]
