from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum
from decimal import Decimal
from houseexpense.core.models import Expense, Deposit, MonthlySummary


@receiver(post_save, sender=Expense)
def update_monthly_summary_on_expense(sender, instance, created, **kwargs):
    """Update monthly summary when expense is created or updated"""
    update_monthly_summary(instance.house, instance.month)


@receiver(post_delete, sender=Expense)
def update_monthly_summary_on_expense_delete(sender, instance, **kwargs):
    """Update monthly summary when expense is deleted"""
    update_monthly_summary(instance.house, instance.month)


@receiver(post_save, sender=Deposit)
def update_monthly_summary_on_deposit(sender, instance, created, **kwargs):
    """Update monthly summary when deposit is created or updated"""
    update_monthly_summary(instance.house, instance.month)


@receiver(post_delete, sender=Deposit)
def update_monthly_summary_on_deposit_delete(sender, instance, **kwargs):
    """Update monthly summary when deposit is deleted"""
    update_monthly_summary(instance.house, instance.month)


def update_monthly_summary(house, month):
    """Calculate and update monthly summary"""
    total_expenses = Expense.objects.filter(
        house=house,
        month=month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    total_deposits = Deposit.objects.filter(
        house=house,
        month=month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    summary, created = MonthlySummary.objects.get_or_create(
        house=house,
        month=month
    )
    summary.total_expenses = total_expenses
    summary.total_deposits = total_deposits
    summary.calculate_balance()
    summary.save()
