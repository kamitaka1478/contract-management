from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from decimal import Decimal
from .models import CustomUser, Contract, BillingRecord, MatchingResult, Alert, ContractFile


class UserSerializer(serializers.ModelSerializer):
    """ユーザーシリアライザー"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 
                 'is_active', 'is_staff', 'password', 'password_confirm', 
                 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError("パスワードが一致しません。")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = CustomUser.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    """ログインシリアライザー"""
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(request=self.context.get('request'),
                              email=email, password=password)
            if not user:
                raise serializers.ValidationError('認証に失敗しました。')
            if not user.is_active:
                raise serializers.ValidationError('アカウントが無効です。')
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('メールアドレスとパスワードを入力してください。')


class ContractFileSerializer(serializers.ModelSerializer):
    """契約ファイルシリアライザー"""
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    
    class Meta:
        model = ContractFile
        fields = ('id', 'file_name', 'file_path', 'file_type', 'file_size', 
                 'uploaded_by', 'uploaded_by_name', 'uploaded_at')
        read_only_fields = ('id', 'uploaded_by', 'uploaded_at')


class ContractSerializer(serializers.ModelSerializer):
    """契約シリアライザー"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    files = ContractFileSerializer(many=True, read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Contract
        fields = ('id', 'contract_number', 'contract_name', 'contractor_name', 
                 'contractor_email', 'contractor_phone', 'contract_start_date', 
                 'contract_end_date', 'contract_amount', 'billing_cycle', 
                 'contract_description', 'contract_status', 'created_by', 
                 'created_by_name', 'files', 'is_active', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at')
    
    def validate_contract_number(self, value):
        """契約番号の重複チェック"""
        if self.instance:
            # 更新時は自分以外との重複をチェック
            if Contract.objects.filter(contract_number=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("この契約番号は既に使用されています。")
        else:
            # 新規作成時
            if Contract.objects.filter(contract_number=value).exists():
                raise serializers.ValidationError("この契約番号は既に使用されています。")
        return value
    
    def validate(self, attrs):
        """契約期間の妥当性チェック"""
        start_date = attrs.get('contract_start_date')
        end_date = attrs.get('contract_end_date')
        
        if start_date and end_date and start_date >= end_date:
            raise serializers.ValidationError("契約終了日は開始日より後の日付を設定してください。")
        
        return attrs


class BillingRecordSerializer(serializers.ModelSerializer):
    """請求記録シリアライザー"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    contract_name = serializers.CharField(source='contract.contract_name', read_only=True)
    contract_number = serializers.CharField(source='contract.contract_number', read_only=True)
    contractor_name = serializers.CharField(source='contract.contractor_name', read_only=True)
    
    class Meta:
        model = BillingRecord
        fields = ('id', 'contract', 'contract_name', 'contract_number', 'contractor_name',
                 'billing_number', 'billing_date', 'due_date', 'billing_amount', 
                 'tax_amount', 'total_amount', 'billing_status', 'billing_description', 
                 'created_by', 'created_by_name', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_by', 'total_amount', 'created_at', 'updated_at')
    
    def validate_billing_number(self, value):
        """請求番号の重複チェック"""
        if self.instance:
            if BillingRecord.objects.filter(billing_number=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("この請求番号は既に使用されています。")
        else:
            if BillingRecord.objects.filter(billing_number=value).exists():
                raise serializers.ValidationError("この請求番号は既に使用されています。")
        return value
    
    def validate(self, attrs):
        """日付の妥当性チェック"""
        billing_date = attrs.get('billing_date')
        due_date = attrs.get('due_date')
        
        if billing_date and due_date and billing_date > due_date:
            raise serializers.ValidationError("支払期限は請求日以降の日付を設定してください。")
        
        return attrs


class MatchingResultSerializer(serializers.ModelSerializer):
    """突合結果シリアライザー"""
    contract_number = serializers.CharField(source='contract.contract_number', read_only=True)
    contract_name = serializers.CharField(source='contract.contract_name', read_only=True)
    billing_number = serializers.CharField(source='billing_record.billing_number', read_only=True)
    resolved_by_name = serializers.CharField(source='resolved_by.get_full_name', read_only=True)
    
    class Meta:
        model = MatchingResult
        fields = ('id', 'contract', 'contract_number', 'contract_name', 
                 'billing_record', 'billing_number', 'matching_status', 
                 'discrepancy_details', 'amount_difference', 'is_resolved', 
                 'resolved_by', 'resolved_by_name', 'resolved_at', 
                 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class AlertSerializer(serializers.ModelSerializer):
    """アラートシリアライザー"""
    contract_number = serializers.CharField(source='contract.contract_number', read_only=True)
    contract_name = serializers.CharField(source='contract.contract_name', read_only=True)
    billing_number = serializers.CharField(source='billing_record.billing_number', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    
    class Meta:
        model = Alert
        fields = ('id', 'contract', 'contract_number', 'contract_name', 
                 'billing_record', 'billing_number', 'matching_result', 
                 'alert_type', 'alert_level', 'alert_title', 'alert_message', 
                 'is_read', 'is_resolved', 'assigned_to', 'assigned_to_name', 
                 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class ContractImportSerializer(serializers.Serializer):
    """契約CSV一括インポート用シリアライザー"""
    file = serializers.FileField()
    
    def validate_file(self, value):
        """ファイル形式チェック"""
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError("CSVファイルをアップロードしてください。")
        
        # ファイルサイズチェック（10MB以下）
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("ファイルサイズは10MB以下にしてください。")
        
        return value


class MatchingExecuteSerializer(serializers.Serializer):
    """突合実行用シリアライザー"""
    contract_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="特定の契約IDのみ突合を実行する場合に指定"
    )
    force_rerun = serializers.BooleanField(
        default=False,
        help_text="既に突合済みの場合も再実行するかどうか"
    )


class DashboardStatsSerializer(serializers.Serializer):
    """ダッシュボード統計情報用シリアライザー"""
    total_contracts = serializers.IntegerField()
    active_contracts = serializers.IntegerField()
    total_billing_records = serializers.IntegerField()
    pending_billing_records = serializers.IntegerField()
    unresolved_alerts = serializers.IntegerField()
    critical_alerts = serializers.IntegerField()
    total_contract_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    monthly_billing_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    matching_accuracy_rate = serializers.FloatField()
    
    class Meta:
        fields = ('total_contracts', 'active_contracts', 'total_billing_records', 
                 'pending_billing_records', 'unresolved_alerts', 'critical_alerts',
                 'total_contract_amount', 'monthly_billing_amount', 'matching_accuracy_rate')


class BulkOperationSerializer(serializers.Serializer):
    """一括操作用シリアライザー"""
    ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        help_text="操作対象のIDリスト"
    )
    action = serializers.ChoiceField(
        choices=[
            ('delete', '削除'),
            ('activate', '有効化'),
            ('deactivate', '無効化'),
            ('resolve', '解決済みにする'),
            ('assign', '担当者割り当て'),
        ],
        help_text="実行するアクション"
    )
    assigned_to = serializers.IntegerField(
        required=False,
        help_text="担当者割り当て時のユーザーID"
    )
    
    def validate(self, attrs):
        action = attrs.get('action')
        assigned_to = attrs.get('assigned_to')
        
        if action == 'assign' and not assigned_to:
            raise serializers.ValidationError("担当者割り当てにはassigned_toが必要です。")
        
        return attrs