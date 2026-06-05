from django import forms
from django.forms import BaseFormSet
from houseexpense.core.models import Expense, Deposit, ExpenseCategory, DepositCategory
from datetime import date
from houseexpense.core.models import Flat


class MonthField(forms.DateField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', forms.DateInput(attrs={'type': 'month', 'class': 'form-control'}, format='%Y-%m'))
        kwargs.setdefault('input_formats', ['%Y-%m'])
        super().__init__(*args, **kwargs)

    def clean(self, value):
        value = super().clean(value)
        if value:
            return date(value.year, value.month, 1)
        return value


class ExpenseEntryForm(forms.ModelForm):
    month = MonthField(label='Month', help_text='Select month for this expense')
    bill_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), label='Bill Date')
    payment_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), label='Payment Date')
    receipt = forms.FileField(required=False, label='Receipt')

    class Meta:
        model = Expense
        fields = ['category', 'amount', 'description', 'month', 'bill_date', 'payment_date', 'receipt']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class DepositEntryForm(forms.ModelForm):
    month = MonthField(label='Month', help_text='Select month for this deposit')
    deposit_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), label='Deposit Date')
    receipt = forms.FileField(required=False, label='Receipt')

    class Meta:
        model = Deposit
        fields = ['flat', 'category', 'amount', 'description', 'month', 'deposit_date', 'receipt']
        widgets = {
            'flat': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        self.house = kwargs.pop('house', None)
        super().__init__(*args, **kwargs)
        self.fields['flat'].required = False
        self.fields['flat'].empty_label = 'Select Flat (optional)'
        self.fields['category'].queryset = DepositCategory.objects.exclude(name='Service Charge')
        if self.house:
            self.fields['flat'].queryset = Flat.objects.filter(house=self.house)
        if not self.instance.pk:
            self.fields['deposit_date'].initial = date.today()
            self.fields['month'].initial = date.today().replace(day=1)
            try:
                self.fields['category'].initial = DepositCategory.objects.get(name='Monthly Parking Income').pk
            except DepositCategory.DoesNotExist:
                pass

    def clean(self):
        cleaned_data = super().clean()
        month = cleaned_data.get('month')
        category = cleaned_data.get('category')
        if self.house and month and category:
            qs = Deposit.objects.filter(house=self.house, month=month, category=category)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    f"A deposit for '{category.name}' in {month.strftime('%B %Y')} already exists."
                )
        return cleaned_data


class MonthlyServiceChargeForm(forms.Form):
    month = MonthField(label='Month', help_text='Select month for service charge', required=True)
    deposit_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Deposit Date',
        required=True
    )
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        label='Amount (leave blank to use flat monthly charge)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )

    flats = forms.ModelMultipleChoiceField(
        queryset=Flat.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label='Select Flats to collect service charge for'
    )

    def __init__(self, *args, **kwargs):
        flats_qs = kwargs.pop('flats_qs', None)
        initial = kwargs.pop('initial', None) or {}
        super().__init__(*args, **kwargs)
        if flats_qs is not None:
            self.fields['flats'].queryset = flats_qs
        else:
            self.fields['flats'].queryset = Flat.objects.none()

        # set initial values when provided
        if 'month' in initial:
            self.fields['month'].initial = initial['month']
        if 'deposit_date' in initial:
            self.fields['deposit_date'].initial = initial['deposit_date']
        if 'amount' in initial:
            self.fields['amount'].initial = initial['amount']


class BatchExpenseMonthForm(forms.Form):
    month = MonthField(label='Month', help_text='Select month for all expenses', required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['month'].widget.attrs['onchange'] = 'this.form.submit()'


class ExpenseCategoryEntryForm(forms.Form):
    category_id = forms.IntegerField(widget=forms.HiddenInput())
    selected = forms.BooleanField(required=False, label='Add this expense')
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        label='Amount'
    )
    bill_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False,
        label='Bill Date'
    )
    payment_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False,
        label='Payment Date'
    )
    receipt = forms.FileField(required=False, label='Receipt')
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        required=False,
        label='Description'
    )

    def __init__(self, *args, **kwargs):
        category = kwargs.pop('category', None)
        super().__init__(*args, **kwargs)
        if category is not None:
            self.fields['category_id'].initial = category.id
            self.fields['category_name'] = forms.CharField(
                initial=category.name,
                widget=forms.HiddenInput()
            )
            self.category_label = category.name
        else:
            self.category_label = ''

    def clean(self):
        cleaned_data = super().clean()
        selected = cleaned_data.get('selected')
        amount = cleaned_data.get('amount')
        bill_date = cleaned_data.get('bill_date')
        payment_date = cleaned_data.get('payment_date')
        receipt = cleaned_data.get('receipt')
        description = cleaned_data.get('description')

        has_data = amount is not None

        if selected or has_data:
            cleaned_data['selected'] = True
            if amount is None:
                self.add_error('amount', 'Amount is required for this expense category.')
            if bill_date is None:
                self.add_error('bill_date', 'Bill Date is required for this expense category.')
            if payment_date is None:
                self.add_error('payment_date', 'Payment Date is required for this expense category.')
        else:
            cleaned_data['selected'] = False

        return cleaned_data


class BaseExpenseCategoryFormSet(BaseFormSet):
    def __init__(self, *args, **kwargs):
        self.categories = kwargs.pop('categories', None)
        super().__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        if self.categories is not None:
            kwargs['category'] = self.categories[i]
        return super()._construct_form(i, **kwargs)


class BatchExpenseEntryForm(forms.Form):
    month = MonthField(label='Month', help_text='Select month for these expenses', required=True)
    bill_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Bill Date',
        required=True
    )
    payment_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Payment Date',
        required=True
    )
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=True,
        label='Amount',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        required=False,
        label='Description'
    )
    categories = forms.ModelMultipleChoiceField(
        queryset=ExpenseCategory.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label='Expense Categories'
    )

    def __init__(self, *args, **kwargs):
        initial = kwargs.pop('initial', None) or {}
        super().__init__(*args, **kwargs)
        if 'month' in initial:
            self.fields['month'].initial = initial['month']
        if 'bill_date' in initial:
            self.fields['bill_date'].initial = initial['bill_date']
        if 'payment_date' in initial:
            self.fields['payment_date'].initial = initial['payment_date']
        if 'amount' in initial:
            self.fields['amount'].initial = initial['amount']
        if 'description' in initial:
            self.fields['description'].initial = initial['description']
