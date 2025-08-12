import React, { useEffect, useState } from 'react';
// import logo from './logo.svg'; // 初期ロゴが必要なければ削除可 → この行を削除
import './App.css'; // 必要なければ削除可

function App() {
  const [contracts, setContracts] = useState([]); // 契約データを保持するステート
  const [loading, setLoading] = useState(true);   // ローディング状態
  const [error, setError] = useState(null);       // エラー状態

  useEffect(() => {
    fetch("http://localhost:8000/api/contracts/")
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
      })
      .then((data) => {
        setContracts(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Fetch error:", err);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="App"><p>Loading contracts...</p></div>;
  }

  if (error) {
    return <div className="App"><p>Error: {error}</p></div>;
  }

  return (
    <div className="App">
      <header className="App-header">
        {/* <img src={logo} className="App-logo" alt="logo" /> → この行を削除 */}
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