from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import MinValueValidator

# Custom User Model
class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('manager', 'Manager'),
        ('flat_owner', 'Flat Owner'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='flat_owner')
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='customuser_set',
        related_query_name='customuser',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='customuser_set',
        related_query_name='customuser',
    )
    
    def is_manager(self):
        return self.role == 'manager'
    
    def is_flat_owner(self):
        return self.role == 'flat_owner'
    
    class Meta:
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"


# House Model
class House(models.Model):
    name = models.CharField(max_length=200, unique=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    total_flats = models.IntegerField()
    manager = models.OneToOneField(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_house',
        limit_choices_to={'role': 'manager'}
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


# Flat Model
class Flat(models.Model):
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='flats')
    flat_number = models.CharField(max_length=50)
    owner = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='flats_owned',
        limit_choices_to={'role': 'flat_owner'}
    )
    carpet_area = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    monthly_charge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    is_occupied = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('house', 'flat_number')
        ordering = ['flat_number']
    
    def __str__(self):
        return f"{self.house.name} - Flat {self.flat_number}"


# Expense Category Model
class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")
    
    class Meta:
        verbose_name_plural = "Expense Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


# Expense Model
class Expense(models.Model):
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='expenses')
    category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    description = models.TextField(blank=True)
    bill_date = models.DateField()
    payment_date = models.DateField()
    month = models.DateField(help_text="First day of the month")
    receipt = models.FileField(upload_to='receipts/expenses/%Y/%m/', blank=True, null=True)
    added_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='expenses_added')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-month', '-bill_date']
        indexes = [
            models.Index(fields=['house', 'month']),
            models.Index(fields=['category', 'month']),
        ]
    
    def __str__(self):
        return f"{self.category.name} - ৳{self.amount} ({self.month.strftime('%B %Y')})"


# Deposit Category Model
class DepositCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Deposit Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


# Deposit Model
class Deposit(models.Model):
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='deposits')
    flat = models.ForeignKey(
        Flat,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deposits'
    )
    category = models.ForeignKey(DepositCategory, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    description = models.TextField(blank=True)
    deposit_date = models.DateField()
    month = models.DateField(help_text="First day of the month")
    receipt = models.FileField(upload_to='receipts/deposits/%Y/%m/', blank=True, null=True)
    added_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='deposits_added')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-month', '-deposit_date']
        indexes = [
            models.Index(fields=['house', 'month']),
            models.Index(fields=['flat', 'month']),
        ]
    
    def __str__(self):
        return f"{self.category.name if self.category else 'Deposit'} - ৳{self.amount} ({self.month.strftime('%B %Y')})"


# Audit Log Model (for tracking changes)
class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.IntegerField()
    changes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user} - {self.get_action_display()} {self.model_name} (ID: {self.object_id})"


# Monthly Summary Model (for caching calculations)
class MonthlySummary(models.Model):
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='monthly_summaries')
    month = models.DateField(help_text="First day of the month")
    total_expenses = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    total_deposits = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('house', 'month')
        ordering = ['-month']
    
    def calculate_balance(self):
        self.balance = self.total_deposits - self.total_expenses
        return self.balance
    
    def __str__(self):
        return f"{self.house.name} - {self.month.strftime('%B %Y')}"
