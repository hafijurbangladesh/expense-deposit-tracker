from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from houseexpense.core.models import House, Expense, Deposit, MonthlySummary
from django.db.models import Sum
from datetime import date, timedelta
from decimal import Decimal


class ReportsHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/reports_home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['is_manager'] = user.is_manager()

        if user.is_manager():
            context['house'] = House.objects.filter(manager=user).first()
        else:
            context['house'] = House.objects.filter(flats__owner=user).distinct().first()

        return context



class FlatWiseReportView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/flat_wise_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        house_id = self.kwargs.get('house_id')
        try:
            house = House.objects.get(id=house_id)
            if user.is_manager():
                if house.manager != user:
                    context['error'] = 'Access denied'
                    return context
            else:
                if not house.flats.filter(owner=user).exists():
                    context['error'] = 'Access denied'
                    return context
            context['house'] = house

            today = date.today()
            selected_year = int(self.request.GET.get('year', today.year))

            deposit_years = Deposit.objects.filter(house=house).dates('month', 'year')
            available_years = sorted(set(d.year for d in deposit_years), reverse=True)
            if today.year not in available_years:
                available_years = [today.year] + list(available_years)

            all_months = [date(selected_year, m, 1) for m in range(1, 13)]

            flats = house.flats.order_by('flat_number')
            flat_data = []

            for flat in flats:
                deposits_qs = Deposit.objects.filter(
                    flat=flat, month__year=selected_year
                ).select_related('category').order_by('month')

                deposits_by_month = {d.month: d for d in deposits_qs}

                month_rows = []
                for month in all_months:
                    deposit = deposits_by_month.get(month)
                    month_rows.append({
                        'month': month,
                        'deposit': deposit,
                        'paid': deposit is not None,
                        'amount': deposit.amount if deposit else None,
                        'deposit_date': deposit.deposit_date if deposit else None,
                        'category': deposit.category.name if deposit and deposit.category else '-',
                    })

                total_collected = deposits_qs.aggregate(t=Sum('amount'))['t'] or Decimal('0.00')
                months_paid = sum(1 for r in month_rows if r['paid'])
                expected_total = flat.monthly_charge * 12

                flat_data.append({
                    'flat': flat,
                    'month_rows': month_rows,
                    'total_collected': total_collected,
                    'months_paid': months_paid,
                    'months_unpaid': 12 - months_paid,
                    'expected_total': expected_total,
                    'collection_rate': round((months_paid / 12) * 100),
                })

            context.update({
                'flat_data': flat_data,
                'selected_year': selected_year,
                'available_years': available_years,
            })

        except House.DoesNotExist:
            context['error'] = 'House not found'

        return context


class MonthWiseReportView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/month_wise_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        house_id = self.kwargs.get('house_id')
        try:
            house = House.objects.get(id=house_id)
            if user.is_manager():
                if house.manager != user:
                    context['error'] = 'Access denied'
                    return context
            else:
                if not house.flats.filter(owner=user).exists():
                    context['error'] = 'Access denied'
                    return context
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
