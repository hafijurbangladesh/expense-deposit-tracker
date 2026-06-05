from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.core.paginator import Paginator
from django.forms import formset_factory
from houseexpense.core.models import House, Expense, Deposit, MonthlySummary, Flat, ExpenseCategory
from houseexpense.core.models import DepositCategory
from houseexpense.dashboard.forms import (
    ExpenseEntryForm,
    DepositEntryForm,
    MonthlyServiceChargeForm,
    BatchExpenseEntryForm,
    BatchExpenseMonthForm,
    ExpenseCategoryEntryForm,
    BaseExpenseCategoryFormSet,
)
from django.utils import timezone
from datetime import timedelta, date
from django.db.models import Sum, F, Value, CharField
from django.db.models.functions import Coalesce, Concat
from decimal import Decimal
import json


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.is_manager():
            # Manager dashboard for a single house
            house = House.objects.filter(manager=user).first()
            context['house'] = house
            context['is_manager'] = True
            
            if house:
                total_expenses = Expense.objects.filter(house=house).aggregate(
                    total=Sum('amount')
                )['total'] or Decimal('0.00')
                total_deposits = Deposit.objects.filter(house=house).aggregate(
                    total=Sum('amount')
                )['total'] or Decimal('0.00')
            else:
                total_expenses = Decimal('0.00')
                total_deposits = Decimal('0.00')
            
            context['total_expenses'] = total_expenses
            context['total_deposits'] = total_deposits
            context['total_balance'] = total_deposits - total_expenses
            
            # Month summary statistics
            today = date.today()
            month_param = self.request.GET.get('summary_month')
            if month_param:
                try:
                    year, month = month_param.split('-')
                    selected_month = date(int(year), int(month), 1)
                except Exception:
                    selected_month = today.replace(day=1)
            else:
                selected_month = today.replace(day=1)
                month_param = selected_month.strftime('%Y-%m')

            if house:
                current_month_expenses = Expense.objects.filter(
                    house=house,
                    month=selected_month
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
                current_month_deposits = Deposit.objects.filter(
                    house=house,
                    month=selected_month
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            else:
                current_month_expenses = Decimal('0.00')
                current_month_deposits = Decimal('0.00')

            context['selected_month'] = selected_month
            context['summary_month_value'] = month_param
            context['current_month_expenses'] = current_month_expenses
            context['current_month_deposits'] = current_month_deposits
            context['current_month_balance'] = current_month_deposits - current_month_expenses
            
            # Recent transactions
            recent_expenses = Expense.objects.filter(house=house).order_by('-created_at')[:5] if house else []
            recent_deposits = Deposit.objects.filter(house=house).order_by('-created_at')[:5] if house else []
            context['recent_expenses'] = recent_expenses
            context['recent_deposits'] = recent_deposits

            context['monthly_deposit_summaries'] = Deposit.objects.filter(
                house=house,
                month=selected_month
            ).values(
                'month'
            ).annotate(
                flat_number=F('flat__flat_number'),
                owner_name=Coalesce(
                    Concat(F('flat__owner__first_name'), Value(' '), F('flat__owner__last_name')),
                    F('flat__owner__username'),
                    Value('N/A'),
                    output_field=CharField()
                ),
                total_deposits=Sum('amount')
            ).order_by('flat_number') if house else []

            context['monthly_expense_summaries'] = Expense.objects.filter(
                house=house,
                month=selected_month
            ).values(
                'category__name'
            ).annotate(
                total_expenses=Sum('amount')
            ).order_by('category__name') if house else []

            # Unpaid flats for current month (Service Charge)
            if house:
                service_cat, _ = DepositCategory.objects.get_or_create(name='Service Charge')
                today = date.today()
                first_day = today.replace(day=1)
                paid_flat_ids = Deposit.objects.filter(house=house, month=first_day, category=service_cat).values_list('flat_id', flat=True)
                unpaid_flats = house.flats.exclude(id__in=paid_flat_ids)
                context['unpaid_flats'] = unpaid_flats
            else:
                context['unpaid_flats'] = []
            
        else:
            # Flat owner dashboard
            flats = user.flats_owned.all()
            context['flats'] = flats
            context['is_manager'] = False
            
            if flats.exists():
                # Get house information
                house = House.objects.filter(flats__in=flats).distinct().first()
                context['house'] = house
                
                # Calculate deposits for this flat owner
                total_deposits = Deposit.objects.filter(flat__in=flats).aggregate(
                    total=Sum('amount')
                )['total'] or Decimal('0.00')
                context['total_deposits'] = total_deposits
                
                # Current month summary
                today = date.today()
                first_day = today.replace(day=1)
                
                context['monthly_deposit_summaries'] = Deposit.objects.filter(flat__in=flats).values(
                    'month'
                ).annotate(
                    flat_number=F('flat__flat_number'),
                    owner_name=Coalesce(
                        Concat(F('flat__owner__first_name'), Value(' '), F('flat__owner__last_name')),
                        F('flat__owner__username'),
                        Value('N/A'),
                        output_field=CharField()
                    ),
                    total_deposits=Sum('amount')
                ).order_by('-month', 'flat_number')
                
                context['current_month_summary'] = MonthlySummary.objects.filter(
                    house=house,
                    month=first_day
                ).first()
        
        return context


class CollectServiceChargeView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/collect_service_charge.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if not user.is_manager():
            context['error'] = 'Access denied'
            return context

        house_id = self.kwargs.get('house_id')
        try:
            house = House.objects.get(id=house_id, manager=user)
        except House.DoesNotExist:
            context['error'] = 'House not found'
            return context

        service_cat, _ = DepositCategory.objects.get_or_create(name='Service Charge')
        today = date.today()
        month_value = self.request.GET.get('month') or self.request.POST.get('month')

        if not month_value:
            month_value = today.strftime('%Y-%m')

        try:
            year, month = month_value.split('-')
            selected_month = date(int(year), int(month), 1)
        except Exception:
            selected_month = today.replace(day=1)
            month_value = selected_month.strftime('%Y-%m')

        paid_flat_ids = Deposit.objects.filter(
            house=house,
            month=selected_month,
            category=service_cat
        ).values_list('flat_id', flat=True)
        paid_flats = house.flats.filter(id__in=paid_flat_ids)
        unpaid_flats = house.flats.exclude(id__in=paid_flat_ids)

        form = MonthlyServiceChargeForm(
            self.request.GET if self.request.GET else None,
            flats_qs=unpaid_flats,
            initial={'month': month_value, 'deposit_date': today}
        )
        
        month_selected = True

        context.update({
            'house': house,
            'form': form,
            'paid_flats': paid_flats,
            'unpaid_flats': unpaid_flats,
            'month_selected': month_selected,
            'selected_month': selected_month,
        })
        return context

    def post(self, request, *args, **kwargs):
        user = request.user
        if not user.is_manager():
            return self.render_to_response({'error': 'Access denied'})

        house_id = self.kwargs.get('house_id')
        try:
            house = House.objects.get(id=house_id, manager=user)
        except House.DoesNotExist:
            return self.render_to_response({'error': 'House not found'})

        service_cat, _ = DepositCategory.objects.get_or_create(name='Service Charge')
        month_value = request.POST.get('month')
        deposit_date_value = request.POST.get('deposit_date')

        try:
            if month_value:
                year, month = month_value.split('-')
                selected_month = date(int(year), int(month), 1)
            else:
                selected_month = date.today().replace(day=1)
        except Exception:
            selected_month = date.today().replace(day=1)

        paid_flat_ids = Deposit.objects.filter(
            house=house,
            month=selected_month,
            category=service_cat
        ).values_list('flat_id', flat=True)
        unpaid_flats = house.flats.exclude(id__in=paid_flat_ids)

        form = MonthlyServiceChargeForm(request.POST, flats_qs=unpaid_flats)

        if form.is_valid():
            flats_selected = form.cleaned_data['flats']
            selected_month = form.cleaned_data['month']
            deposit_date = form.cleaned_data['deposit_date']
            amount_override = form.cleaned_data.get('amount')

            for flat in flats_selected:
                if not Deposit.objects.filter(
                    house=house,
                    flat=flat,
                    month=selected_month,
                    category=service_cat
                ).exists():
                    amt = amount_override if amount_override is not None else flat.monthly_charge
                    Deposit.objects.create(
                        house=house,
                        flat=flat,
                        category=service_cat,
                        amount=amt,
                        description='Monthly Service Charge',
                        deposit_date=deposit_date,
                        month=selected_month,
                        added_by=user
                    )
            return redirect('dashboard:dashboard')

        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)


class HouseExpenseDepositView(LoginRequiredMixin, TemplateView):
    """View to add/manage expenses and deposits for a house"""
    template_name = 'dashboard/house_transactions.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if not user.is_manager():
            return {'error': 'Access denied'}
        
        house_id = self.kwargs.get('house_id')
        try:
            house = House.objects.get(id=house_id, manager=user)
            context['house'] = house
            
            context['expenses'] = Expense.objects.filter(house=house).order_by('-created_at')[:10]
            all_deposits = Deposit.objects.filter(house=house).order_by('-month', '-deposit_date')
            paginator = Paginator(all_deposits, 10)
            page_number = self.request.GET.get('page', 1)
            context['deposits'] = paginator.get_page(page_number)
            context['flats'] = house.flats.all()
            context['deposit_form'] = DepositEntryForm(house=house)
            used = Deposit.objects.filter(house=house).values('month', 'category_id')
            used_map = {}
            for item in used:
                key = item['month'].strftime('%Y-%m')
                used_map.setdefault(key, []).append(item['category_id'])
            context['used_combinations'] = json.dumps(used_map)
            
        except House.DoesNotExist:
            context['error'] = 'House not found'
        
        return context

    def post(self, request, *args, **kwargs):
        user = request.user
        if not user.is_manager():
            return {'error': 'Access denied'}

        house_id = self.kwargs.get('house_id')
        try:
            house = House.objects.get(id=house_id, manager=user)
        except House.DoesNotExist:
            return self.render_to_response({'error': 'House not found'})

        if request.POST.get('form_type') == 'deposit':
            form = DepositEntryForm(request.POST, request.FILES, house=house)
            if form.is_valid():
                deposit = form.save(commit=False)
                deposit.house = house
                deposit.added_by = user
                deposit.save()
                return redirect('dashboard:add_deposit', house_id=house.id)
            context = self.get_context_data(**kwargs)
            context['deposit_form'] = form
            return self.render_to_response(context)

        if request.POST.get('form_type') == 'edit_deposit':
            deposit_id = request.POST.get('deposit_id')
            try:
                deposit = Deposit.objects.get(id=deposit_id, house=house)
            except Deposit.DoesNotExist:
                context = self.get_context_data(**kwargs)
                context['error_msg'] = 'Deposit not found.'
                return self.render_to_response(context)
            form = DepositEntryForm(request.POST, request.FILES, instance=deposit, house=house)
            if form.is_valid():
                form.save()
                return redirect('dashboard:add_deposit', house_id=house.id)
            context = self.get_context_data(**kwargs)
            context['edit_form'] = form
            context['edit_deposit_id'] = int(deposit_id)
            return self.render_to_response(context)

        return self.render_to_response(self.get_context_data(**kwargs))


class AddExpensesView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/add_expenses.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if not user.is_manager():
            context['error'] = 'Access denied'
            return context

        house_id = self.kwargs.get('house_id')
        try:
            house = House.objects.get(id=house_id, manager=user)
        except House.DoesNotExist:
            context['error'] = 'House not found'
            return context

        today = date.today()
        first_day = today.replace(day=1)
        month_value = self.request.GET.get('month') or self.request.POST.get('month')
        if month_value:
            try:
                year, month = month_value.split('-')
                selected_month = date(int(year), int(month), 1)
            except Exception:
                selected_month = first_day
                month_value = first_day.strftime('%Y-%m')
        else:
            selected_month = first_day
            month_value = selected_month.strftime('%Y-%m')

        categories = ExpenseCategory.objects.all()
        existing_expenses = Expense.objects.filter(house=house, month=selected_month).select_related('category')
        paid_categories = {}
        for expense in existing_expenses:
            paid_categories.setdefault(expense.category_id, []).append(expense)

        ExpenseFormSet = formset_factory(
            ExpenseCategoryEntryForm,
            formset=BaseExpenseCategoryFormSet,
            extra=0,
            can_delete=False
        )
        initial = [{'category_id': category.id, 'bill_date': today, 'payment_date': today} for category in categories]
        formset = ExpenseFormSet(
            initial=initial,
            categories=list(categories),
            prefix='expenses'
        )

        for form in formset:
            category_id = form.initial.get('category_id')
            if category_id in paid_categories:
                form.paid = True
                form.paid_entries = paid_categories[category_id]
                form.fields['selected'].disabled = True
                form.fields['amount'].disabled = True
                form.fields['bill_date'].disabled = True
                form.fields['payment_date'].disabled = True
                form.fields['receipt'].disabled = True
                form.fields['description'].disabled = True
            else:
                form.paid = False
                form.paid_entries = []

        month_form = BatchExpenseMonthForm(self.request.GET or self.request.POST or None, initial={'month': selected_month})

        all_expenses = Expense.objects.filter(house=house).order_by('-month', '-payment_date').select_related('category')
        grouped = {}
        for expense in all_expenses:
            key = expense.month
            grouped.setdefault(key, []).append(expense)
        grouped_list = [{'month': m, 'expenses': grouped[m]} for m in sorted(grouped.keys(), reverse=True)]
        paginator = Paginator(grouped_list, 1)
        page_number = self.request.GET.get('page', 1)
        expense_history = paginator.get_page(page_number)

        context.update({
            'house': house,
            'selected_month': selected_month,
            'month_form': month_form,
            'expense_formset': formset,
            'expense_history': expense_history,
            'expense_months': [g['month'] for g in grouped_list],
            'expense_categories': ExpenseCategory.objects.all(),
        })
        return context

    def post(self, request, *args, **kwargs):
        user = request.user
        if not user.is_manager():
            return self.render_to_response({'error': 'Access denied'})

        house_id = self.kwargs.get('house_id')
        try:
            house = House.objects.get(id=house_id, manager=user)
        except House.DoesNotExist:
            return self.render_to_response({'error': 'House not found'})

        categories = ExpenseCategory.objects.all()
        ExpenseFormSet = formset_factory(
            ExpenseCategoryEntryForm,
            formset=BaseExpenseCategoryFormSet,
            extra=0,
            can_delete=False
        )
        month_form = BatchExpenseMonthForm(request.POST)
        expense_formset = ExpenseFormSet(
            request.POST,
            request.FILES,
            categories=list(categories),
            prefix='expenses'
        )

        if request.POST.get('form_type') == 'edit_expense':
            expense_id = request.POST.get('expense_id')
            try:
                expense = Expense.objects.get(id=expense_id, house=house)
            except Expense.DoesNotExist:
                context = self.get_context_data(**kwargs)
                context['edit_expense_error'] = 'Expense not found.'
                return self.render_to_response(context)
            edit_form = ExpenseEntryForm(request.POST, request.FILES, instance=expense)
            if edit_form.is_valid():
                edit_form.save()
                redirect_url = f"{request.path}?month={expense.month.strftime('%Y-%m')}"
                return redirect(redirect_url)
            context = self.get_context_data(**kwargs)
            context['edit_expense_form'] = edit_form
            context['edit_expense_id'] = int(expense_id)
            return self.render_to_response(context)

        if month_form.is_valid() and expense_formset.is_valid():
            month = month_form.cleaned_data['month']
            created = 0
            for form in expense_formset:
                if form.cleaned_data.get('selected'):
                    category_id = form.cleaned_data['category_id']
                    category = ExpenseCategory.objects.get(id=category_id)
                    Expense.objects.create(
                        house=house,
                        category=category,
                        amount=form.cleaned_data['amount'],
                        description=form.cleaned_data.get('description', ''),
                        bill_date=form.cleaned_data['bill_date'],
                        payment_date=form.cleaned_data['payment_date'],
                        month=month,
                        receipt=form.cleaned_data.get('receipt'),
                        added_by=user
                    )
                    created += 1
            if created:
                redirect_url = f"{request.path}?month={month.strftime('%Y-%m')}"
                return redirect(redirect_url)
        context = self.get_context_data(**kwargs)
        context['month_form'] = month_form
        context['expense_formset'] = expense_formset
        return self.render_to_response(context)


class MonthlyReportView(LoginRequiredMixin, TemplateView):
    """View monthly report for a house"""
    template_name = 'dashboard/monthly_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if not user.is_manager():
            return {'error': 'Access denied'}
        
        house_id = self.kwargs.get('house_id')
        month_str = self.kwargs.get('month', None)
        
        try:
            house = House.objects.get(id=house_id, manager=user)
            context['house'] = house
            
            if month_str:
                # Parse month from string (YYYY-MM)
                year, month = map(int, month_str.split('-'))
                first_day = date(year, month, 1)
            else:
                today = date.today()
                first_day = today.replace(day=1)
            
            context['month'] = first_day
            context['summary'] = MonthlySummary.objects.get_or_create(
                house=house,
                month=first_day
            )[0]
            
            context['expenses'] = Expense.objects.filter(house=house, month=first_day)
            context['deposits'] = Deposit.objects.filter(house=house, month=first_day)
            
        except House.DoesNotExist:
            context['error'] = 'House not found'
        
        return context
