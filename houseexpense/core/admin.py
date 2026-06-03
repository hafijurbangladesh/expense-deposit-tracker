from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from houseexpense.core.models import (
    CustomUser, House, Flat, ExpenseCategory, Expense,
    DepositCategory, Deposit, AuditLog, MonthlySummary
)

@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'get_full_name', 'role', 'is_active')
    list_filter = ('role', 'is_active', 'date_joined')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('role', 'phone', 'address')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Custom Fields', {'fields': ('role', 'phone', 'address')}),
    )


@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'total_flats', 'manager', 'created_at')
    list_filter = ('city', 'created_at')
    search_fields = ('name', 'address', 'city')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Flat)
class FlatAdmin(admin.ModelAdmin):
    list_display = ('get_house', 'flat_number', 'owner', 'monthly_charge', 'is_occupied')
    list_filter = ('house', 'is_occupied')
    search_fields = ('flat_number', 'owner__username')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_house(self, obj):
        return obj.house.name
    get_house.short_description = 'House'


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('get_house', 'category', 'amount', 'month', 'payment_date')
    list_filter = ('house', 'category', 'month')
    search_fields = ('category__name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'month'
    
    def get_house(self, obj):
        return obj.house.name
    get_house.short_description = 'House'


@admin.register(DepositCategory)
class DepositCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ('get_house', 'get_flat', 'category', 'amount', 'month', 'deposit_date')
    list_filter = ('house', 'flat', 'category', 'month')
    search_fields = ('description', 'flat__flat_number')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'month'
    
    def get_house(self, obj):
        return obj.house.name
    get_house.short_description = 'House'
    
    def get_flat(self, obj):
        return obj.flat.flat_number if obj.flat else '-'
    get_flat.short_description = 'Flat'


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'model_name', 'object_id', 'timestamp')
    list_filter = ('action', 'model_name', 'timestamp')
    readonly_fields = ('user', 'action', 'model_name', 'object_id', 'changes', 'timestamp')
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(MonthlySummary)
class MonthlySummaryAdmin(admin.ModelAdmin):
    list_display = ('get_house', 'month', 'total_deposits', 'total_expenses', 'balance')
    list_filter = ('house', 'month')
    readonly_fields = ('updated_at', 'balance')
    
    def get_house(self, obj):
        return obj.house.name
    get_house.short_description = 'House'
