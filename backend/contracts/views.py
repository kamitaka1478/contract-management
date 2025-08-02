from django.http import JsonResponse

def contract_list(request):
    # ここでデータベースから契約データを取得するロジックを記述します
    # 今はテスト用にダミーデータを返します
    data = [
        {"id": 1, "client_name": "株式会社A", "amount": 100000, "start_date": "2023-01-01", "end_date": "2023-12-31"},
        {"id": 2, "client_name": "株式会社B", "amount": 50000, "start_date": "2023-03-15", "end_date": "2024-03-14"},
    ]
    return JsonResponse(data, safe=False) # safe=False はリストを返す場合に必要
