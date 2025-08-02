from django.urls import path
from . import views # 同じディレクトリのviews.pyからインポート

urlpatterns = [
    path('', views.contract_list, name='contract_list'),
    # 必要であれば、詳細取得や登録/更新/削除のためのパスもここに追加
    # path('<int:pk>/', views.contract_detail, name='contract_detail'),
]