from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class CustomUser(AbstractUser):
    """カスタムユーザーモデル"""
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        db_table = 'users'


class Contract(models.Model):
    """契約情報モデル"""
    
    BILLING_CYCLES = [
        ('monthly', '月次'),
        ('quarterly', '四半期'),
        ('semi_annual', '半年'),
        ('annual', '年次'),
        ('one_time', '一回限り'),
    ]
    
    STATUS_CHOICES = [
        ('draft', '下書き'),
        ('active', '有効'),
        ('expired', '期限切れ'),
        ('terminated', '解約済み'),
        ('suspended', '停止中'),
    ]
    
    id = models.AutoField(primary_key=True)
    contract_number = models.CharField(max_length=50, unique=True, verbose_name='契約番号')
    contract_name = models.CharField(max_length=200, verbose_name='契約名')
    contractor_name = models.CharField(max_length=100, verbose_name='契約者名')
    contractor_email = models.EmailField(verbose_name='契約者メール')
    contractor_phone = models.CharField(max_length=20, blank=True, verbose_name='契約者電話番号')
    
    contract_start_date = models.DateField(verbose_name='契約開始日')
    contract_end_date = models.DateField(verbose_name='契約終了日')
    contract_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='契約金額'
    )
    billing_cycle = models.CharField(
        max_length=20, 
        choices=BILLING_CYCLES, 
        default='monthly',
        verbose_name='請求サイクル'
    )
    contract_description = models.TextField(blank=True, verbose_name='契約詳細')
    contract_status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='draft',
        verbose_name='契約ステータス'
    )
    
    created_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.PROTECT, 
        related_name='created_contracts',
        verbose_name='作成者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')
    
    class Meta:
        db_table = 'contracts'
        verbose_name = '契約'
        verbose_name_plural = '契約'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.contract_number} - {self.contract_name}"
    
    @property
    def is_active(self):
        """契約が有効かどうか"""
        from django.utils import timezone
        today = timezone.now().date()
        return (
            self.contract_status == 'active' and
            self.contract_start_date <= today <= self.contract_end_date
        )


class BillingRecord(models.Model):
    """請求情報モデル"""
    
    STATUS_CHOICES = [
        ('draft', '下書き'),
        ('sent', '送信済み'),
        ('paid', '支払済み'),
        ('overdue', '期限超過'),
        ('cancelled', 'キャンセル'),
    ]
    
    id = models.AutoField(primary_key=True)
    contract = models.ForeignKey(
        Contract, 
        on_delete=models.PROTECT, 
        related_name='billing_records',
        verbose_name='契約'
    )
    billing_number = models.CharField(max_length=50, unique=True, verbose_name='請求番号')
    billing_date = models.DateField(verbose_name='請求日')
    due_date = models.DateField(verbose_name='支払期限')
    
    billing_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='請求金額（税抜き）'
    )
    tax_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        default=Decimal('0.00'),
        verbose_name='税額'
    )
    total_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='請求総額（税込み）'
    )
    
    billing_status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='draft',
        verbose_name='請求ステータス'
    )
    billing_description = models.TextField(blank=True, verbose_name='請求詳細')
    
    created_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.PROTECT, 
        related_name='created_billing_records',
        verbose_name='作成者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')
    
    class Meta:
        db_table = 'billing_records'
        verbose_name = '請求記録'
        verbose_name_plural = '請求記録'
        ordering = ['-billing_date']
    
    def __str__(self):
        return f"{self.billing_number} - {self.contract.contract_name}"
    
    def save(self, *args, **kwargs):
        """保存時に税込み総額を自動計算"""
        if self.billing_amount and self.tax_amount:
            self.total_amount = self.billing_amount + self.tax_amount
        super().save(*args, **kwargs)


class MatchingResult(models.Model):
    """突合結果モデル"""
    
    STATUS_CHOICES = [
        ('matched', '一致'),
        ('amount_mismatch', '金額不一致'),
        ('date_mismatch', '日付不一致'),
        ('cycle_violation', 'サイクル違反'),
        ('contract_expired', '契約期限切れ'),
        ('multiple_issues', '複数問題'),
    ]
    
    id = models.AutoField(primary_key=True)
    contract = models.ForeignKey(
        Contract, 
        on_delete=models.CASCADE, 
        related_name='matching_results',
        verbose_name='契約'
    )
    billing_record = models.ForeignKey(
        BillingRecord, 
        on_delete=models.CASCADE, 
        related_name='matching_results',
        verbose_name='請求記録'
    )
    
    matching_status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES,
        verbose_name='突合ステータス'
    )
    discrepancy_details = models.TextField(blank=True, verbose_name='不一致詳細')
    amount_difference = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        null=True, 
        blank=True,
        verbose_name='金額差異'
    )
    
    is_resolved = models.BooleanField(default=False, verbose_name='解決済み')
    resolved_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='resolved_matching_results',
        verbose_name='解決者'
    )
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name='解決日時')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')
    
    class Meta:
        db_table = 'matching_results'
        verbose_name = '突合結果'
        verbose_name_plural = '突合結果'
        ordering = ['-created_at']
        unique_together = ['contract', 'billing_record']
    
    def __str__(self):
        return f"突合結果: {self.contract.contract_number} - {self.matching_status}"


class Alert(models.Model):
    """アラートモデル"""
    
    ALERT_TYPES = [
        ('amount_mismatch', '金額不一致'),
        ('missing_billing', '請求漏れ'),
        ('duplicate_billing', '重複請求'),
        ('contract_expiry', '契約期限'),
        ('overdue_payment', '支払遅延'),
    ]
    
    ALERT_LEVELS = [
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
        ('critical', '緊急'),
    ]
    
    id = models.AutoField(primary_key=True)
    contract = models.ForeignKey(
        Contract, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='alerts',
        verbose_name='契約'
    )
    billing_record = models.ForeignKey(
        BillingRecord, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='alerts',
        verbose_name='請求記録'
    )
    matching_result = models.ForeignKey(
        MatchingResult, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='alerts',
        verbose_name='突合結果'
    )
    
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES, verbose_name='アラート種別')
    alert_level = models.CharField(max_length=10, choices=ALERT_LEVELS, verbose_name='アラートレベル')
    alert_title = models.CharField(max_length=200, verbose_name='アラートタイトル')
    alert_message = models.TextField(verbose_name='アラートメッセージ')
    
    is_read = models.BooleanField(default=False, verbose_name='既読')
    is_resolved = models.BooleanField(default=False, verbose_name='解決済み')
    assigned_to = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_alerts',
        verbose_name='担当者'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')
    
    class Meta:
        db_table = 'alerts'
        verbose_name = 'アラート'
        verbose_name_plural = 'アラート'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.alert_level}: {self.alert_title}"


class ContractFile(models.Model):
    """契約ファイルモデル"""
    
    id = models.AutoField(primary_key=True)
    contract = models.ForeignKey(
        Contract, 
        on_delete=models.CASCADE, 
        related_name='files',
        verbose_name='契約'
    )
    file_name = models.CharField(max_length=255, verbose_name='ファイル名')
    file_path = models.CharField(max_length=500, verbose_name='ファイルパス')
    file_type = models.CharField(max_length=50, verbose_name='ファイル種別')
    file_size = models.PositiveIntegerField(verbose_name='ファイルサイズ（バイト）')
    
    uploaded_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.PROTECT,
        related_name='uploaded_contract_files',
        verbose_name='アップロード者'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='アップロード日時')
    
    class Meta:
        db_table = 'contract_files'
        verbose_name = '契約ファイル'
        verbose_name_plural = '契約ファイル'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.contract.contract_number} - {self.file_name}"


class AuditLog(models.Model):
    """監査ログモデル"""
    
    ACTION_TYPES = [
        ('create', '作成'),
        ('update', '更新'),
        ('delete', '削除'),
        ('login', 'ログイン'),
        ('logout', 'ログアウト'),
        ('export', 'エクスポート'),
        ('import', 'インポート'),
    ]
    
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='audit_logs',
        verbose_name='ユーザー'
    )
    action_type = models.CharField(max_length=10, choices=ACTION_TYPES, verbose_name='アクション種別')
    table_name = models.CharField(max_length=50, verbose_name='テーブル名')
    record_id = models.PositiveIntegerField(null=True, blank=True, verbose_name='レコードID')
    old_values = models.JSONField(null=True, blank=True, verbose_name='変更前の値')
    new_values = models.JSONField(null=True, blank=True, verbose_name='変更後の値')
    ip_address = models.GenericIPAddressField(verbose_name='IPアドレス')
    user_agent = models.TextField(blank=True, verbose_name='ユーザーエージェント')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    
    class Meta:
        db_table = 'audit_logs'
        verbose_name = '監査ログ'
        verbose_name_plural = '監査ログ'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user} - {self.action_type} - {self.table_name}"