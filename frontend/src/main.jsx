import React from "react";
import { createRoot } from "react-dom/client";
import "./index.css";

async function api(path, options) {
  const r = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options?.headers || {}) },
    ...options
  });
  const text = await r.text();
  const data = text ? JSON.parse(text) : null;
  if (!r.ok) {
    const message = data?.error?.message || `HTTP ${r.status}`;
    const details = data?.error ? `\n${JSON.stringify(data.error, null, 2)}` : "";
    throw new Error(message + details);
  }
  return data;
}

function App() {
  const [error, setError] = React.useState(null);
  const [products, setProducts] = React.useState([]);
  const [selectedId, setSelectedId] = React.useState(null);
  const [movements, setMovements] = React.useState([]);
  const [movementsNextCursor, setMovementsNextCursor] = React.useState(null);

  const [newSku, setNewSku] = React.useState("");
  const [newName, setNewName] = React.useState("");
  const [newThreshold, setNewThreshold] = React.useState("5");

  const [moveType, setMoveType] = React.useState("receive");
  const [moveDirection, setMoveDirection] = React.useState("increase");
  const [moveQty, setMoveQty] = React.useState("1");
  const [moveNote, setMoveNote] = React.useState("");

  const [lowStock, setLowStock] = React.useState([]);

  async function refreshProducts() {
    const list = await api("/api/products");
    setProducts(list);
    if (list.length && selectedId == null) setSelectedId(list[0].id);
  }

  async function refreshMovements(productId) {
    if (!productId) return;
    const res = await api(`/api/products/${productId}/movements?limit=20`);
    setMovements(res.items);
    setMovementsNextCursor(res.next_cursor);
  }

  async function refreshLowStock() {
    const list = await api("/api/alerts/low-stock");
    setLowStock(list);
  }

  React.useEffect(() => {
    (async () => {
      try {
        setError(null);
        await api("/api/health");
        await refreshProducts();
        await refreshLowStock();
      } catch (e) {
        setError(String(e));
      }
    })();
  }, []);

  React.useEffect(() => {
    (async () => {
      try {
        setError(null);
        await refreshMovements(selectedId);
        await refreshLowStock();
      } catch (e) {
        setError(String(e));
      }
    })();
  }, [selectedId]);

  async function onCreateProduct(e) {
    e.preventDefault();
    try {
      setError(null);
      const created = await api("/api/products", {
        method: "POST",
        body: JSON.stringify({
          sku: newSku.trim(),
          name: newName.trim(),
          low_stock_threshold: Number(newThreshold)
        })
      });
      setNewSku("");
      setNewName("");
      setSelectedId(created.id);
      await refreshProducts();
      await refreshLowStock();
    } catch (e2) {
      setError(String(e2));
    }
  }

  async function onCreateMovement(e) {
    e.preventDefault();
    if (!selectedId) return;
    try {
      setError(null);
      const payload = {
        type: moveType,
        quantity: Number(moveQty),
        note: moveNote.trim() ? moveNote.trim() : null
      };
      if (moveType === "adjust") payload.direction = moveDirection;
      await api(`/api/products/${selectedId}/movements`, {
        method: "POST",
        body: JSON.stringify(payload)
      });
      setMoveNote("");
      await refreshProducts();
      await refreshMovements(selectedId);
      await refreshLowStock();
    } catch (e2) {
      setError(String(e2));
    }
  }

  async function onLoadMoreMovements() {
    if (!selectedId || !movementsNextCursor) return;
    try {
      setError(null);
      const res = await api(`/api/products/${selectedId}/movements?limit=20&cursor=${movementsNextCursor}`);
      setMovements((prev) => [...prev, ...res.items]);
      setMovementsNextCursor(res.next_cursor);
    } catch (e2) {
      setError(String(e2));
    }
  }

  return (
    <div className="min-h-screen">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <div>
            <div className="text-lg font-semibold leading-6">Inventory Tracker</div>
            <div className="text-sm text-slate-600">Ledger-based stock with low-stock alerts</div>
          </div>
          <div className="text-xs text-slate-500">Backend: `http://localhost:5001`</div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6">
        {error ? (
          <div className="mb-6 rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900">
            <div className="font-semibold">Something went wrong</div>
            <pre className="mt-2 whitespace-pre-wrap text-xs leading-5">{error}</pre>
          </div>
        ) : null}

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <section className="rounded-xl border bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-base font-semibold">Products</h2>
              <button
                type="button"
                className="rounded-md border px-3 py-1.5 text-sm hover:bg-slate-50"
                onClick={() => {
                  refreshProducts().catch((e) => setError(String(e)));
                  refreshLowStock().catch((e) => setError(String(e)));
                }}
              >
                Refresh
              </button>
            </div>

            <form onSubmit={onCreateProduct} className="mb-5 grid gap-3">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                <div className="sm:col-span-1">
                  <label className="text-xs font-medium text-slate-600">SKU</label>
                  <input
                    className="mt-1 w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring"
                    placeholder="SKU-1001"
                    value={newSku}
                    onChange={(e) => setNewSku(e.target.value)}
                  />
                </div>
                <div className="sm:col-span-2">
                  <label className="text-xs font-medium text-slate-600">Name</label>
                  <input
                    className="mt-1 w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring"
                    placeholder="Product name"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                  />
                </div>
              </div>
              <div className="flex items-end gap-3">
                <div className="w-48">
                  <label className="text-xs font-medium text-slate-600">Low stock threshold</label>
                  <input
                    className="mt-1 w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring"
                    inputMode="numeric"
                    value={newThreshold}
                    onChange={(e) => setNewThreshold(e.target.value)}
                  />
                </div>
                <button
                  type="submit"
                  disabled={!newSku.trim() || !newName.trim()}
                  className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
                >
                  Add product
                </button>
              </div>
            </form>

            <div className="overflow-hidden rounded-lg border">
              {products.length === 0 ? (
                <div className="p-4 text-sm text-slate-600">No products yet. Add one above.</div>
              ) : (
                <ul className="divide-y">
                  {products.map((p) => {
                    const isSelected = p.id === selectedId;
                    const isLow = p.current_stock <= p.low_stock_threshold;
                    return (
                      <li
                        key={p.id}
                        onClick={() => setSelectedId(p.id)}
                        className={[
                          "cursor-pointer p-4 transition",
                          isSelected ? "bg-slate-50" : "hover:bg-slate-50"
                        ].join(" ")}
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div>
                            <div className="text-sm font-semibold">
                              {p.sku} <span className="font-normal text-slate-500">—</span> {p.name}
                            </div>
                            <div className="mt-0.5 text-xs text-slate-600">Low stock ≤ {p.low_stock_threshold}</div>
                          </div>
                          <div className="text-right">
                            <div className="text-sm font-semibold tabular-nums">Stock: {p.current_stock}</div>
                            {isLow ? (
                              <div className="mt-1 inline-flex rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-900">
                                Low
                              </div>
                            ) : (
                              <div className="mt-1 inline-flex rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-900">
                                OK
                              </div>
                            )}
                          </div>
                        </div>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          </section>

          <section className="rounded-xl border bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-base font-semibold">Stock movements</h2>
              <div className="text-xs text-slate-500">Paginated (cursor)</div>
            </div>

            {!selectedId ? (
              <div className="rounded-lg border border-dashed p-6 text-sm text-slate-600">Select a product to begin.</div>
            ) : (
              <>
                <form onSubmit={onCreateMovement} className="mb-5 grid gap-3">
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                    <div>
                      <label className="text-xs font-medium text-slate-600">Type</label>
                      <select
                        className="mt-1 w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring"
                        value={moveType}
                        onChange={(e) => setMoveType(e.target.value)}
                      >
                        <option value="receive">receive</option>
                        <option value="ship">ship</option>
                        <option value="adjust">adjust</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-xs font-medium text-slate-600">Direction</label>
                      <select
                        className="mt-1 w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring disabled:bg-slate-50"
                        value={moveDirection}
                        onChange={(e) => setMoveDirection(e.target.value)}
                        disabled={moveType !== "adjust"}
                      >
                        <option value="increase">increase</option>
                        <option value="decrease">decrease</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-xs font-medium text-slate-600">Quantity</label>
                      <input
                        className="mt-1 w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring"
                        inputMode="numeric"
                        value={moveQty}
                        onChange={(e) => setMoveQty(e.target.value)}
                      />
                    </div>
                  </div>
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
                    <div className="flex-1">
                      <label className="text-xs font-medium text-slate-600">Note (optional)</label>
                      <input
                        className="mt-1 w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring"
                        placeholder="e.g. Shipment #123"
                        value={moveNote}
                        onChange={(e) => setMoveNote(e.target.value)}
                      />
                    </div>
                    <button
                      type="submit"
                      className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
                    >
                      Add movement
                    </button>
                  </div>
                </form>

                <div className="overflow-hidden rounded-lg border">
                  {movements.length === 0 ? (
                    <div className="p-4 text-sm text-slate-600">No movements yet.</div>
                  ) : (
                    <ul className="divide-y">
                      {movements.map((m) => (
                        <li key={m.id} className="p-4">
                          <div className="flex items-start justify-between gap-4">
                            <div>
                              <div className="text-sm font-semibold">
                                {m.type}
                                {m.type === "adjust" ? (
                                  <span className="ml-2 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">
                                    {m.direction}
                                  </span>
                                ) : null}
                              </div>
                              <div className="mt-1 text-xs text-slate-500">{m.created_at}</div>
                              {m.note ? <div className="mt-2 text-sm text-slate-700">{m.note}</div> : null}
                            </div>
                            <div className="text-right tabular-nums">
                              <div className="text-sm font-semibold">qty: {m.quantity}</div>
                            </div>
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                {movementsNextCursor ? (
                  <button
                    className="mt-4 w-full rounded-md border bg-white px-4 py-2 text-sm font-medium hover:bg-slate-50"
                    onClick={onLoadMoreMovements}
                  >
                    Load more
                  </button>
                ) : null}

                <div className="mt-6">
                  <div className="mb-2 flex items-center justify-between">
                    <h3 className="text-sm font-semibold">Low stock</h3>
                    <span className="text-xs text-slate-500">{lowStock.length} item(s)</span>
                  </div>
                  <div className="overflow-hidden rounded-lg border">
                    {lowStock.length === 0 ? (
                      <div className="p-4 text-sm text-slate-600">No low-stock alerts.</div>
                    ) : (
                      <ul className="divide-y">
                        {lowStock.map((p) => (
                          <li key={p.id} className="p-4">
                            <div className="flex items-start justify-between gap-4">
                              <div>
                                <div className="text-sm font-semibold">
                                  {p.sku} <span className="font-normal text-slate-500">—</span> {p.name}
                                </div>
                                <div className="mt-1 text-xs text-slate-600">
                                  Stock <span className="font-semibold tabular-nums">{p.current_stock}</span> (threshold{" "}
                                  <span className="font-semibold tabular-nums">{p.low_stock_threshold}</span>)
                                </div>
                              </div>
                              <div className="inline-flex rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-900">
                                Restock
                              </div>
                            </div>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              </>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

