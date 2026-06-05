from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from houseexpense.core.models import House, Expense, Deposit, MonthlySummary, ExpenseCategory
from django.db.models import Sum
from datetime import date, timedelta
from decimal import Decimal
import json
from itertools import groupby


class ReportsHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/reports_home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.is_manager():
            context['house'] = House.objects.filter(manager=user).first()
            context['is_manager'] = True
        else:
            context['is_manager'] = False
        
        return context


class ExpenseCategoryReportView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/expense_category_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if not user.is_manager():
            return {'error': 'Access denied'}
        
        house_id = self.kwargs.get('house_id')
        try:
            house = House.objects.get(id=house_id, manager=user)
            context['house'] = house
            
            # Get all expenses grouped by category
            expenses_by_category = Expense.objects.filter(house=house).values(
                'category__name'
            ).annotate(total=Sum('amount')).order_by('-total')
            
            context['expenses_by_category'] = expenses_by_category
            
            # Get top expense categories
            context['top_categories'] = list(expenses_by_category[:5])
            
        except House.DoesNotExist:
            context['error'] = 'House not found'
        
        return context


class AnnualReportView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/annual_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if not user.is_manager():
            return {'error': 'Access denied'}
        
        house_id = self.kwargs.get('house_id')
        try:
            house = House.objects.get(id=house_id, manager=user)
            context['house'] = house
            
            # Get last 12 months
            today = date.today()
            twelve_months_ago = today - timedelta(days=365)
            
            summaries = MonthlySummary.objects.filter(
                house=house,
                month__gte=twelve_months_ago
            ).order_by('month')
            
            context['monthly_summaries'] = summaries
            
            # Calculate totals
            total_expenses = sum([s.total_expenses for s in summaries])
            total_deposits = sum([s.total_deposits for s in summaries])
            
            context['total_expenses'] = total_expenses
            context['total_deposits'] = total_deposits
            context['total_balance'] = total_deposits - total_expenses
            
        except House.DoesNotExist:
            context['error'] = 'House not found'
        
        return context


class FlatWiseReportView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/flat_wise_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if not user.is_manager():
            return {'error': 'Access denied'}
        
        house_id = self.kwargs.get('house_id')
        try:
            house = House.objects.get(id=house_id, manager=user)
            context['house'] = house
            
            # Get deposits by flat
            flats_deposits = Deposit.objects.filter(house=house).values(
                'flat__flat_number'
            ).annotate(total=Sum('amount')).order_by('-total')
            
            context['flats_deposits'] = flats_deposits
            
            # Get all flats with their charges
            flats = house.flats.all()
            flat_data = []
            for flat in flats:
                deposits = Deposit.objects.filter(flat=flat).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
                flat_data.append({
                    'flat': flat,
                    'total_deposits': deposits,
                })
            
            context['flat_data'] = flat_data
            
        except House.DoesNotExist:
            context['error'] = 'House not found'
        
        return context


class MonthWiseReportView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/month_wise_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if not user.is_manager():
            context['error'] = 'Access denied'
            return context

        house_id = self.kwargs.get('house_id')
        try:
            house = House.objects.get(id=house_id, manager=user)
            context['house'] = house

            # Year filter
            today = date.today()
            selected_year = int(self.request.GET.get('year', today.year))

            all_deposit_months = Deposit.objects.filter(house=house).dates('month', 'year')
            all_expense_months = Expense.objects.filter(house=house).dates('month', 'year')
            available_years = sorted(
                set([d.year for d in all_deposit_months] + [d.year for d in all_expense_months]),
                reverse=True
            )
            if not available_years:
                available_years = [today.year]

            # Get all months with transactions for selected year
            deposit_months = set(
                Deposit.objects.filter(house=house, month__year=selected_year)
                .values_list('month', flat=True).distinct()
            )
            expense_months = set(
                Expense.objects.filter(house=house, month__year=selected_year)
                .values_list('month', flat=True).distinct()
            )
            all_months = sorted(deposit_months | expense_months, reverse=True)

            # Build month-wise data
            months_data = []
            grand_total_deposits = Decimal('0.00')
            grand_total_expenses = Decimal('0.00')

            for month in all_months:
                deposits = Deposit.objects.filter(house=house, month=month).select_related('category', 'flat').order_by('category__name')
                expenses = Expense.objects.filter(house=house, month=month).select_related('category').order_by('category__name')

                total_deposits = deposits.aggregate(t=Sum('amount'))['t'] or Decimal('0.00')
                total_expenses = expenses.aggregate(t=Sum('amount'))['t'] or Decimal('0.00')
                balance = total_deposits - total_expenses

                grand_total_deposits += total_deposits
                grand_total_expenses += total_expenses

                months_data.append({
                    'month': month,
                    'deposits': list(deposits),
                    'expenses': list(expenses),
                    'total_deposits': total_deposits,
                    'total_expenses': total_expenses,
                    'balance': balance,
                })

            context.update({
                'months_data': months_data,
                'selected_year': selected_year,
                'available_years': available_years,
                'grand_total_deposits': grand_total_deposits,
                'grand_total_expenses': grand_total_expenses,
                'grand_balance': grand_total_deposits - grand_total_expenses,
            })

        except House.DoesNotExist:
            context['error'] = 'House not found'

        return context


class ChartDataAPIView(LoginRequiredMixin, TemplateView):
    """API endpoint for chart data"""
    
    def get(self, request, *args, **kwargs):
        user = request.user
        
        if not user.is_manager():
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        house_id = request.GET.get('house_id')
        chart_type = request.GET.get('type', 'monthly')
        
        try:
            house = House.objects.get(id=house_id, manager=user)
            
            if chart_type == 'monthly':
                data = self._get_monthly_chart_data(house)
            elif chart_type == 'category':
                data = self._get_category_chart_data(house)
            else:
                data = {'error': 'Invalid chart type'}
            
            return JsonResponse(data)
        
        except House.DoesNotExist:
            return JsonResponse({'error': 'House not found'}, status=404)
    
    def _get_monthly_chart_data(self, house):
        # Get last 12 months
        today = date.today()
        months = []
        expenses = []
        deposits = []
        
        for i in range(11, -1, -1):
            month_date = today.replace(day=1) - timedelta(days=i*30)
            month_date = month_date.replace(day=1)
            
            summary = MonthlySummary.objects.filter(house=house, month=month_date).first()
            
            months.append(month_date.strftime('%b %Y'))
            expenses.append(float(summary.total_expenses if summary else 0))
            deposits.append(float(summary.total_deposits if summary else 0))
        
        return {
            'labels': months,
            'expenses': expenses,
            'deposits': deposits,
        }
    
    def _get_category_chart_data(self, house):
        expenses_by_category = Expense.objects.filter(house=house).values(
            'category__name'
        ).annotate(total=Sum('amount')).order_by('-total')[:5]
        
        categories = [item['category__name'] for item in expenses_by_category]
        amounts = [float(item['total']) for item in expenses_by_category]
        
        return {
            'labels': categories,
            'amounts': amounts,
        }
