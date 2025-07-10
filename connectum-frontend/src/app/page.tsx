"use client";

import { useState } from "react";
import styles from "./page.module.css";

interface BoardResponse {
  board: number[][];
  winner: number | null;
  turn: number;
  valid_moves: number[];
  scores?: number[];
}

const API_URL = "http://localhost:8000"; // Change if backend runs elsewhere
const difficulties = ["easy", "medium", "hard", "impossible"];
const starters = ["player", "bot"];

export default function Home() {
  const [state, setState] = useState<BoardResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [setup, setSetup] = useState(true);
  const [difficulty, setDifficulty] = useState("impossible");
  const [whoStarts, setWhoStarts] = useState("player");
  const [trainingMode, setTrainingMode] = useState(false);

  // Start game only after setup
  const startGame = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ difficulty, who_starts: whoStarts, training_mode: trainingMode }),
      });
      if (!res.ok) throw new Error("Failed to start game");
      setState(await res.json());
      setSetup(false);
    } catch {
      setError("Could not connect to backend");
    } finally {
      setLoading(false);
    }
  };

  const makeMove = async (col: number) => {
    if (!state || !state.valid_moves.includes(col) || state.winner !== null) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/move`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ column: col }),
      });
      if (!res.ok) throw new Error("Invalid move");
      setState(await res.json());
    } catch (e) {
      setError("Move failed");
    } finally {
      setLoading(false);
    }
  };

  const reset = async () => {
    setLoading(true);
    setError(null);
    try {
      await fetch(`${API_URL}/reset`, { method: "POST" });
      setState(null);
      setSetup(true);
    } catch {
      setError("Reset failed");
    } finally {
      setLoading(false);
    }
  };

return (
    <div className={styles.page} style={{ minHeight: 600, minWidth: 1024, width: 1024, height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#1e293b', overflow: 'hidden', padding: 0 }}>
      <div style={{ width: 600, height: '95%', maxWidth: 600, maxHeight: '95vh', padding: 0, boxShadow: '0 4px 24px #0008', borderRadius: 20, background: '#22223b', display: 'flex', flexDirection: 'column', justifyContent: 'flex-start', alignItems: 'center', overflow: 'hidden' }}>
        <main className={styles.main} style={{ alignItems: 'center', justifyContent: 'flex-start', padding: 0, width: '100%', height: '100%', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          <h1 style={{ fontSize: 28, fontWeight: 700, margin: '8px 0 2px 0', textAlign: 'center', letterSpacing: 2, color: '#f8fafc' }}>ConnecTUM</h1>
          {error && <div style={{ color: "#f87171", marginBottom: 6 }}>{error}</div>}
          {setup ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'center', width: '100%' }}>
              <div style={{ width: '100%' }}>
                <label htmlFor="difficulty" style={{ fontWeight: 600, fontSize: 18, color: '#f8fafc' }}>Difficulty</label>
                <select id="difficulty" value={difficulty} onChange={e => setDifficulty(e.target.value)} style={{ width: '100%', fontSize: 18, padding: 8, borderRadius: 8, marginTop: 4, background: '#2d314d', color: '#f8fafc', border: '1px solid #475569' }}>
                  {difficulties.map(d => <option key={d} value={d}>{d}</option>)}
                </select>
              </div>
              <div style={{ width: '100%' }}>
                <label htmlFor="whoStarts" style={{ fontWeight: 600, fontSize: 18, color: '#f8fafc' }}>Who starts</label>
                <select id="whoStarts" value={whoStarts} onChange={e => setWhoStarts(e.target.value)} style={{ width: '100%', fontSize: 18, padding: 8, borderRadius: 8, marginTop: 4, background: '#2d314d', color: '#f8fafc', border: '1px solid #475569' }}>
                  {starters.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              <div style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 0 }}>
                <input type="checkbox" id="trainingMode" checked={trainingMode} onChange={e => setTrainingMode(e.target.checked)} style={{ width: 20, height: 20 }} />
                <label htmlFor="trainingMode" style={{ fontWeight: 600, fontSize: 18, color: '#f8fafc' }}>Training Mode</label>
              </div>
              <button onClick={startGame} disabled={loading} style={{ width: '100%', fontSize: 20, marginTop: 8, padding: '12px 0', borderRadius: 12, background: '#2563eb', color: '#fff', border: 'none', fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.7 : 1, boxShadow: '0 2px 8px #0004' }}>Start Game</button>
            </div>
          ) :
          (!state || !state.board || !Array.isArray(state.board) || state.board.length === 0 ? (
            <div>Loading...</div>
          ) : (
            <>
              <div style={{ marginBottom: 2, marginTop: 2, fontSize: 18, minHeight: 24, color: '#f8fafc', fontWeight: 600, textAlign: 'center' }}>
                {state.winner !== null && (
                  <span style={{ marginLeft: 8 }}>
                    <b>Winner:</b> {state.winner === -1 ? "Player" : state.winner === 1 ? "Bot" : state.winner === 0 ? "Draw" : ""}
                  </span>
                )}
              </div>
              <div style={{
                display: "grid",
                gridTemplateColumns: `repeat(${state.board[0].length}, 48px)`,
                gap: 2,
                margin: '0 auto 2px auto',
                background: '#232946',
                borderRadius: 10,
                padding: 2,
                maxHeight: 'calc(100vh - 250px)',
                overflow: 'hidden',
                boxSizing: 'border-box',
                justifyContent: 'center',
              }}>
                {state.board.map((row, rowIdx) =>
                  row.map((cell, colIdx) => (
                    <button
                      key={`${rowIdx}-${colIdx}`}
                      style={{
                        width: 48,
                        height: 48,
                        borderRadius: "50%",
                        background: cell === 0 ? "#e0e7ef" : cell === 1 ? "#f43f5e" : "#facc15",
                        border: state.valid_moves.includes(colIdx) ? "2px solid #38bdf8" : "1px solid #64748b",
                        cursor: state.valid_moves.includes(colIdx) && !loading && state.winner === null ? "pointer" : "default",
                        boxShadow: cell !== 0 ? '0 2px 8px #0002' : undefined,
                        fontSize: 14,
                        fontWeight: 700,
                        color: cell === 1 ? '#fff' : cell === -1 ? '#222' : '#222',
                        outline: 'none',
                        transition: 'background 0.2s, border 0.2s',
                        margin: 0,
                        padding: 0,
                      }}
                      disabled={loading || !state.valid_moves.includes(colIdx) || state.winner !== null}
                      onClick={() => makeMove(colIdx)}
                      aria-label={`Drop in column ${colIdx + 1}`}
                    />
                  ))
                )}
              </div>
              {trainingMode && state.scores && (
                <div style={{ width: '100%', color: '#f8fafc', fontSize: 16, fontWeight: 700, overflow: 'hidden', textOverflow: 'ellipsis', textAlign: 'center' }}>
                  <b>Impossible mode scores:</b>
                  <div style={{ display: "flex", gap: 4, marginTop: 2, justifyContent: 'center', flexWrap: 'wrap', fontWeight: 400, fontSize: 13 }}>
                    {state.scores.map((score: number, idx: number) => (
                      <span key={idx} style={{
                        display: 'inline-block',
                        color: '#f8fafc',
                        fontSize: 16,
                        fontWeight: 700,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        textAlign: 'center',
                        padding: '2px 8px',
                        borderRadius: 6,
                        background: '#232946'
                      }}>{Math.round(score)}</span>
                    ))}
                  </div>
                </div>
              )}
              <button onClick={reset} disabled={loading} style={{ width: '100%', fontSize: 16, marginTop: 8, padding: '8px 0', borderRadius: 8, background: '#f59e42', color: '#fff', border: 'none', fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.7 : 1, boxShadow: '0 2px 8px #0004' }}>Reset Game</button>
            </>
          ))}
        </main>
      </div>
    </div>
  );

}
