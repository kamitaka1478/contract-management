from rest_framework import generics, status, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import login, logout
from django.db import transaction
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
import csv
import io
import logging

from .models import CustomUser, Contract, BillingRecord, MatchingResult, Alert, ContractFile
from .serializers import (
    UserSerializer, LoginSerializer, ContractSerializer, BillingRecordSerializer,
    MatchingResultSerializer, AlertSerializer, ContractImportSerializer,
    MatchingExecuteSerializer, DashboardStatsSerializer, BulkOperationSerializer
)
from .services import MatchingService, NotificationService
from .filters import ContractFilter, BillingRecordFilter, AlertFilter

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    """標準ペジネーション設定"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# 認証関連ビュー
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    """ログインAPI"""
    serializer = LoginSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = serializer.validated_data['user']
        login(request, user)
        token, created = Token.objects.get_or_create(user=user)
        
        # ログイン履歴を記録
        from .utils import create_audit_log
        create_audit_log(user, 'login', 'users', user.id, request)
        
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
            'message': 'ログインに成功しました。'
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """ログアウトAPI"""
    try:
        # トークンを削除
        request.user.auth_token.delete()
        logout(request)
        
        # ログアウト履歴を記録
        from .utils import create_audit_log
        create_audit_log(request.user, 'logout', 'users', request.user.id, request)
        
        return Response({'message': 'ログアウトしました。'})
    except Exception as e:
        logger.error(f"ログアウトエラー: {e}")
        return Response({'error': 'ログアウトに失敗しました。'}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 契約管理ビュー
class ContractListCreateView(generics.ListCreateAPIView):
    """契約一覧取得・新規作成API"""
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchBackend, filters.OrderingFilter]
    filterset_class = ContractFilter
    search_fields = ['contract_name', 'contractor_name', 'contract_number']
    ordering_fields = ['created_at', 'contract_start_date', 'contract_amount']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        """作成時にユーザー情報を自動設定"""
        contract = serializer.save(created_by=self.request.user)
        
        # 監査ログ記録
        from .utils import create_audit_log
        create_audit_log(self.request.user, 'create', 'contracts', contract.id, self.request)


class ContractDetailView(generics.RetrieveUpdateDestroyAPIView):
    """契約詳細取得・更新・削除API"""
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_update(self, serializer):
        """更新時の監査ログ記録"""
        old_data = ContractSerializer(self.get_object()).data
        contract = serializer.save()
        new_data = ContractSerializer(contract).data
        
        from .utils import create_audit_log
        create_audit_log(self.request.user, 'update', 'contracts', contract.id, 
                        self.request, old_data, new_data)
    
    def perform_destroy(self, instance):
        """削除時の監査ログ記録"""
        from .utils import create_audit_log
        create_audit_log(self.request.user, 'delete', 'contracts', instance.id, self.request)
        instance.delete()


# 請求管理ビュー
class BillingRecordListCreateView(generics.ListCreateAPIView):
    """請求記録一覧取得・新規作成API"""
    queryset = BillingRecord.objects.select_related('contract', 'created_by')
    serializer_class = BillingRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchBackend, filters.OrderingFilter]
    filterset_class = BillingRecordFilter
    search_fields = ['billing_number', 'contract__contract_name', 'contract__contractor_name']
    ordering_fields = ['billing_date', 'due_date', 'total_amount', 'created_at']
    ordering = ['-billing_date']
    
    def perform_create(self, serializer):
        """作成時にユーザー情報を自動設定し、突合処理を実行"""
        billing_record = serializer.save(created_by=self.request.user)
        
        # 監査ログ記録
        from .utils import create_audit_log
        create_audit_log(self.request.user, 'create', 'billing_records', 
                        billing_record.id, self.request)
        
        # 自動突合処理を非同期で実行
        try:
            matching_service = MatchingService()
            matching_service.run_matching_for_billing(billing_record)
        except Exception as e:
            logger.error(f"突合処理エラー: {e}")


class BillingRecordDetailView(generics.RetrieveUpdateDestroyAPIView):
    """請求記録詳細取得・更新・削除API"""
    queryset = BillingRecord.objects.select_related('contract', 'created_by')
    serializer_class = BillingRecordSerializer
    permission_classes = [permissions.IsAuthenticated]


# 突合結果ビュー
class MatchingResultListView(generics.ListAPIView):
    """突合結果一覧取得API"""
    queryset = MatchingResult.objects.select_related('contract', 'billing_record', 'resolved_by')
    serializer_class = MatchingResultSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['matching_status', 'is_resolved']
    ordering_fields = ['created_at', 'amount_difference']
    ordering = ['-created_at']


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def execute_matching(request):
    """突合処理実行API"""
    serializer = MatchingExecuteSerializer(data=request.data)
    if serializer.is_valid():
        try:
            matching_service = MatchingService()
            contract_ids = serializer.validated_data.get('contract_ids')
            force_rerun = serializer.validated_data.get('force_rerun', False)
            
            if contract_ids:
                # 特定契約の突合
                contracts = Contract.objects.filter(id__in=contract_ids)
                results = matching_service.run_matching_for_contracts(contracts, force_rerun)
            else:
                # 全契約の突合
                results = matching_service.run_full_matching(force_rerun)
            
            return Response({
                'message': '突合処理が完了しました。',
                'processed_count': results['processed_count'],
                'matched_count': results['matched_count'],
                'mismatched_count': results['mismatched_count'],
                'error_count': results['error_count']
            })
        
        except Exception as e:
            logger.error(f"突合処理実行エラー: {e}")
            return Response({'error': '突合処理に失敗しました。'}, 
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# アラート管理ビュー
class AlertListView(generics.ListAPIView):
    """アラート一覧取得API"""
    queryset = Alert.objects.select_related('contract', 'billing_record', 'assigned_to')
    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = AlertFilter
    ordering_fields = ['created_at', 'alert_level']
    ordering = ['-created_at']


@api_view(['PATCH'])
@permission_classes([permissions.IsAuthenticated])
def mark_alert_read(request, alert_id):
    """アラート既読マークAPI"""
    try:
        alert = Alert.objects.get(id=alert_id)
        alert.is_read = True
        alert.save()
        return Response({'message': 'アラートを既読にしました。'})
    except Alert.DoesNotExist:
        return Response({'error': 'アラートが見つかりません。'}, 
                       status=status.HTTP_404_NOT_FOUND)


@api_view(['PATCH'])
@permission_classes([permissions.IsAuthenticated])
def resolve_alert(request, alert_id):
    """アラート解決API"""
    try:
        alert = Alert.objects.get(id=alert_id)
        alert.is_resolved = True
        alert.assigned_to = request.user
        alert.save()
        return Response({'message': 'アラートを解決済みにしました。'})
    except Alert.DoesNotExist:
        return Response({'error': 'アラートが見つかりません。'}, 
                       status=status.HTTP_404_NOT_FOUND)


# CSV インポート
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def import_contracts_csv(request):
    """契約CSV一括インポートAPI"""
    serializer = ContractImportSerializer(data=request.data)
    if serializer.is_valid():
        csv_file = serializer.validated_data['file']
        
        try:
            # CSVファイルを読み込み
            file_data = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(file_data))
            
            success_count = 0
            error_count = 0
            errors = []
            
            with transaction.atomic():
                for row_num, row in enumerate(csv_reader, start=2):  # ヘッダー行があるので2から
                    try:
                        # 必須フィールドチェック
                        required_fields = ['contract_number', 'contract_name', 'contractor_name', 
                                         'contract_start_date', 'contract_end_date', 'contract_amount']
                        
                        for field in required_fields:
                            if not row.get(field):
                                raise ValidationError(f"必須フィールド '{field}' が空です。")
                        
                        # 日付フィールドの変換
                        from datetime import datetime
                        start_date = datetime.strptime(row['contract_start_date'], '%Y-%m-%d').date()
                        end_date = datetime.strptime(row['contract_end_date'], '%Y-%m-%d').date()
                        
                        # 契約データ作成
                        contract = Contract.objects.create(
                            contract_number=row['contract_number'],
                            contract_name=row['contract_name'],
                            contractor_name=row['contractor_name'],
                            contractor_email=row.get('contractor_email', ''),
                            contractor_phone=row.get('contractor_phone', ''),
                            contract_start_date=start_date,
                            contract_end_date=end_date,
                            contract_amount=Decimal(row['contract_amount']),
                            billing_cycle=row.get('billing_cycle', 'monthly'),
                            contract_description=row.get('contract_description', ''),
                            contract_status=row.get('contract_status', 'active'),
                            created_by=request.user
                        )
                        success_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        errors.append(f"行 {row_num}: {str(e)}")
            
            # 監査ログ記録
            from .utils import create_audit_log
            create_audit_log(request.user, 'import', 'contracts', None, request)
            
            return Response({
                'message': f'CSVインポートが完了しました。成功: {success_count}件、エラー: {error_count}件',
                'success_count': success_count,
                'error_count': error_count,
                'errors': errors
            })
        
        except Exception as e:
            logger.error(f"CSVインポートエラー: {e}")
            return Response({'error': 'CSVファイルの処理に失敗しました。'}, 
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ダッシュボード統計API
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_stats(request):
    """ダッシュボード統計情報取得API"""
    try:
        # 基本統計
        total_contracts = Contract.objects.count()
        active_contracts = Contract.objects.filter(contract_status='active').count()
        total_billing_records = BillingRecord.objects.count()
        pending_billing = BillingRecord.objects.filter(billing_status__in=['draft', 'sent']).count()
        
        # アラート統計
        unresolved_alerts = Alert.objects.filter(is_resolved=False).count()
        critical_alerts = Alert.objects.filter(alert_level='critical', is_resolved=False).count()
        
        # 金額統計
        total_amount = Contract.objects.aggregate(total=Sum('contract_amount'))['total'] or 0
    except Exception as e:
        logger.error(f"ダッシュボード統計取得エラー: {e}")
        return Response({'error': '統計情報の取得に失敗しました。'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)