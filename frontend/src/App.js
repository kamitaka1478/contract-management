import React, { useEffect, useState } from 'react';
import './App.css'; // 必要なければ削除可

function App() {
  const [contracts, setContracts] = useState([]); // 契約データを保持するステート
  const [loading, setLoading] = useState(true);   // ローディング状態
  const [error, setError] = useState(null);      // エラー状態

  useEffect(() => {
    // APIから契約一覧を取得
    // ここでDjangoバックエンドのAPIを呼び出します
    fetch("http://localhost:8000/api/contracts/")
      .then((res) => {
        if (!res.ok) {
          // HTTPステータスが200番台以外の場合
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
      })
      .then((data) => {
        setContracts(data);
        setLoading(false);
      })
      .catch((err) => {
        // ネットワークエラーなど、fetch自体が失敗した場合
        console.error("Fetch error:", err); // デバッグ用にコンソールに出力
        setError(err.message);
        setLoading(false);
      });
  }, []); // 依存配列が空なので、コンポーネントがマウントされた時に一度だけ実行

  if (loading) {
    return <div className="App"><p>Loading contracts...</p></div>;
  }

  if (error) {
    return <div className="App"><p>Error: {error}</p></div>;
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>契約一覧</h1>
        {contracts.length > 0 ? (
          <ul>
            {contracts.map((contract) => (
              <li key={contract.id}>
                {contract.client_name} - {contract.amount}円 ({contract.start_date} ~ {contract.end_date})
              </li>
            ))}
          </ul>
        ) : (
          <p>No contracts found.</p>
        )}
      </header>
    </div>
  );
}

export default App;