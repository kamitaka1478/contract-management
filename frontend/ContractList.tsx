import React, { useEffect, useState } from "react";

type Contract = {
  id: number;
  name: string;
  start_date: string;
  end_date: string;
};

const ContractList: React.FC = () => {
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // APIから契約一覧を取得
    fetch("/api/contracts/")
      .then((res) => {
        if (!res.ok) throw new Error("データ取得失敗");
        return res.json();
      })
      .then((data) => {
        setContracts(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) return <div>読み込み中...</div>;
  if (error) return <div className="text-red-500">{error}</div>;

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">契約一覧</h1>
      <table className="min-w-full border border-gray-300">
        <thead className="bg-gray-100">
          <tr>
            <th className="border px-4 py-2">ID</th>
            <th className="border px-4 py-2">契約名</th>
            <th className="border px-4 py-2">開始日</th>
            <th className="border px-4 py-2">終了日</th>
          </tr>
        </thead>
        <tbody>
          {contracts.map((contract) => (
            <tr key={contract.id}>
              <td className="border px-4 py-2">{contract.id}</td>
              <td className="border px-4 py-2">{contract.name}</td>
              <td className="border px-4 py-2">{contract.start_date}</td>
              <td className="border px-4 py-2">{contract.end_date}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ContractList;