"use client";

import {useState, useEffect} from "react";
import styles from "./page.module.css";

interface BoardResponse {
    board: number[][];
    winner: number | null;
    turn: number;
    valid_moves: number[];
    scores?: number[];
}

interface MagazineStatus {
    magazine1_full: boolean;
    magazine2_full: boolean;
}

const API_URL = "http://localhost:8000"; // Change if backend runs elsewhere

function StartingScreen({
                            difficulty,
                            setDifficulty,
                            whoStarts,
                            setWhoStarts,
                            trainingMode,
                            setTrainingMode,
                            startGame,
                            loading,
                            error,
                            goToLeaderboard,
                            nickname,
                            setNickname,
                        }: {
    difficulty: string;
    setDifficulty: (d: string) => void;
    whoStarts: string;
    setWhoStarts: (s: string) => void;
    trainingMode: boolean;
    setTrainingMode: (b: boolean) => void;
    startGame: () => void;
    loading: boolean;
    error: string | null;
    goToLeaderboard: () => void;
    nickname: string;
    setNickname: (n: string) => void;
}) {
    const difficulties = ["easy", "medium", "hard", "impossible"];
    const starters = ["player", "bot"];
    return (
        <div style={{display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'center', width: '100%'}}>
            <h1 style={{
                fontSize: 28,
                fontWeight: 700,
                margin: '8px 0 2px 0',
                textAlign: 'center',
                letterSpacing: 2,
                color: '#f8fafc'
            }}>ConnecTUM</h1>
            {error && <div style={{color: "#f87171", marginBottom: 6}}>{error}</div>}
            <div style={{width: '100%'}}>
                <label htmlFor="nickname" style={{fontWeight: 600, fontSize: 18, color: '#f8fafc'}}>Nickname</label>
                <input
                    id="nickname"
                    type="text"
                    value={nickname}
                    onChange={e => setNickname(e.target.value.slice(0, 15))}
                    maxLength={15}
                    style={{
                        width: '100%',
                        fontSize: 18,
                        padding: 8,
                        borderRadius: 8,
                        marginTop: 4,
                        background: '#2d314d',
                        color: '#f8fafc',
                        border: '1px solid #475569'
                    }}
                    placeholder="Enter nickname (max 15 chars)"
                />
            </div>
            <div style={{width: '100%'}}>
                <label htmlFor="difficulty" style={{fontWeight: 600, fontSize: 18, color: '#f8fafc'}}>Difficulty</label>
                <select id="difficulty" value={difficulty} onChange={e => setDifficulty(e.target.value)} style={{
                    width: '100%',
                    fontSize: 18,
                    padding: 8,
                    borderRadius: 8,
                    marginTop: 4,
                    background: '#2d314d',
                    color: '#f8fafc',
                    border: '1px solid #475569'
                }}>
                    {difficulties.map(d => <option key={d} value={d}>{d}</option>)}
                </select>
            </div>
            <div style={{width: '100%'}}>
                <label htmlFor="whoStarts" style={{fontWeight: 600, fontSize: 18, color: '#f8fafc'}}>Who starts</label>
                <select id="whoStarts" value={whoStarts} onChange={e => setWhoStarts(e.target.value)} style={{
                    width: '100%',
                    fontSize: 18,
                    padding: 8,
                    borderRadius: 8,
                    marginTop: 4,
                    background: '#2d314d',
                    color: '#f8fafc',
                    border: '1px solid #475569'
                }}>
                    {starters.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
            </div>
            <div style={{width: '100%', display: 'flex', alignItems: 'center', gap: 0}}>
                <input type="checkbox" id="trainingMode" checked={trainingMode}
                       onChange={e => setTrainingMode(e.target.checked)} style={{width: 20, height: 20}}/>
                <label htmlFor="trainingMode" style={{fontWeight: 600, fontSize: 18, color: '#f8fafc'}}>Training
                    Mode</label>
            </div>
            <button onClick={startGame} disabled={loading} style={{
                width: '100%',
                fontSize: 20,
                marginTop: 8,
                padding: '12px 0',
                borderRadius: 12,
                background: '#2563eb',
                color: '#fff',
                border: 'none',
                fontWeight: 700,
                cursor: loading ? 'not-allowed' : 'pointer',
                opacity: loading ? 0.7 : 1,
                boxShadow: '0 2px 8px #0004'
            }}>Start Game
            </button>
            <button onClick={goToLeaderboard} style={{
                width: '100%',
                fontSize: 16,
                marginTop: 8,
                padding: '8px 0',
                borderRadius: 8,
                background: '#38bdf8',
                color: '#fff',
                border: 'none',
                fontWeight: 700,
                cursor: 'pointer',
                boxShadow: '0 2px 8px #0004'
            }}>Leaderboard
            </button>
        </div>
    );
}

function GameScreen({
                        state,
                        loading,
                        error,
                        makeMove,
                        reset,
                        trainingMode,
                        goToStart,
                    }: {
    state: BoardResponse;
    loading: boolean;
    error: string | null;
    makeMove: (col: number) => void;
    reset: () => void;
    trainingMode: boolean;
    goToStart: () => void;
}) {
    return (
        <>
            <h1 style={{
                fontSize: 28,
                fontWeight: 700,
                margin: '8px 0 2px 0',
                textAlign: 'center',
                letterSpacing: 2,
                color: '#f8fafc'
            }}>ConnecTUM</h1>
            {error && <div style={{color: "#f87171", marginBottom: 6}}>{error}</div>}
            <div style={{
                marginBottom: 2,
                marginTop: 2,
                fontSize: 18,
                minHeight: 24,
                color: '#f8fafc',
                fontWeight: 600,
                textAlign: 'center'
            }}>
                {state.winner !== null && (
                    <span style={{marginLeft: 8}}>
            <b>Winner:</b> {state.winner === -1 ? "Player" : state.winner === 1 ? "Bot" : state.winner === 0 ? "Draw" : ""}
          </span>
                )}
            </div>
            {trainingMode && state.scores && (
                <div style={{
                    width: '100%',
                    color: '#f8fafc',
                    fontSize: 16,
                    fontWeight: 700,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    textAlign: 'center',
                    marginBottom: 8
                }}>
                    <b>Impossible mode scores:</b>
                    <div style={{
                        display: "flex",
                        gap: 4,
                        marginTop: 2,
                        justifyContent: 'center',
                        flexWrap: 'wrap',
                        fontWeight: 400,
                        fontSize: 13
                    }}>
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
            <button onClick={reset} disabled={loading} style={{
                width: '100%',
                fontSize: 16,
                marginTop: 8,
                padding: '8px 0',
                borderRadius: 8,
                background: '#f59e42',
                color: '#fff',
                border: 'none',
                fontWeight: 700,
                cursor: loading ? 'not-allowed' : 'pointer',
                opacity: loading ? 0.7 : 1,
                boxShadow: '0 2px 8px #0004'
            }}>Reset Game
            </button>
        </>
    );
}

function LeaderboardScreen({goToStart}: { goToStart: () => void }) {
    // Mock leaderboard data
    const leaderboard = [
        {name: "Alice", score: 120},
        {name: "Bob", score: 110},
        {name: "Carol", score: 100},
    ];
    return (
        <div style={{width: '100%', textAlign: 'center', color: '#f8fafc'}}>
            <h1 style={{
                fontSize: 28,
                fontWeight: 700,
                margin: '8px 0 2px 0',
                textAlign: 'center',
                letterSpacing: 2
            }}>Leaderboard</h1>
            <table style={{
                width: '80%',
                margin: '0 auto',
                background: '#232946',
                borderRadius: 10,
                color: '#f8fafc',
                fontSize: 18
            }}>
                <thead>
                <tr style={{fontWeight: 700}}>
                    <th style={{padding: 8}}>Name</th>
                    <th style={{padding: 8}}>Score</th>
                </tr>
                </thead>
                <tbody>
                {leaderboard.map((entry, idx) => (
                    <tr key={idx}>
                        <td style={{padding: 8}}>{entry.name}</td>
                        <td style={{padding: 8}}>{entry.score}</td>
                    </tr>
                ))}
                </tbody>
            </table>
            <button onClick={goToStart} style={{
                width: '80%',
                fontSize: 16,
                marginTop: 16,
                padding: '8px 0',
                borderRadius: 8,
                background: '#64748b',
                color: '#fff',
                border: 'none',
                fontWeight: 700,
                cursor: 'pointer',
                boxShadow: '0 2px 8px #0004'
            }}>Back to Start
            </button>
        </div>
    );
}

// Error Dialog Component
function ErrorDialog({
                        isOpen,
                        message,
                        onClose
                    }: {
    isOpen: boolean;
    message: string;
    onClose: () => void;
}) {
    if (!isOpen) return null;

    // Determine title based on message content
    const getTitle = () => {
        if (message.includes('Cannot start game')) return 'Cannot Start Game';
        if (message.includes('Cannot make move')) return 'Cannot Make Move';
        if (message.includes('session on the server was lost')) return 'Game Session Lost';
        return 'Error';
    };

    return (
        <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '20px'
        }}>
            <div style={{
                backgroundColor: '#1e293b',
                borderRadius: '16px',
                padding: '32px',
                maxWidth: '400px',
                width: '100%',
                border: '2px solid #ef4444',
                boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)',
                color: '#f8fafc'
            }}>
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    marginBottom: '16px'
                }}>
                    <div style={{
                        width: '48px',
                        height: '48px',
                        borderRadius: '50%',
                        backgroundColor: '#ef4444',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        marginRight: '16px',
                        fontSize: '24px'
                    }}>
                        ⚠️
                    </div>
                    <h3 style={{
                        fontSize: '20px',
                        fontWeight: '700',
                        margin: 0,
                        color: '#f8fafc'
                    }}>
                        {getTitle()}
                    </h3>
                </div>
                <p style={{
                    fontSize: '16px',
                    lineHeight: '1.5',
                    marginBottom: '24px',
                    color: '#cbd5e1'
                }}>
                    {message}
                </p>
                <div style={{
                    display: 'flex',
                    justifyContent: 'flex-end'
                }}>
                    <button
                        onClick={onClose}
                        style={{
                            backgroundColor: '#3b82f6',
                            color: 'white',
                            border: 'none',
                            borderRadius: '8px',
                            padding: '12px 24px',
                            fontSize: '16px',
                            fontWeight: '600',
                            cursor: 'pointer',
                            boxShadow: '0 4px 8px rgba(59, 130, 246, 0.3)',
                            transition: 'background-color 0.2s'
                        }}
                        onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#2563eb'}
                        onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#3b82f6'}
                    >
                        Understood
                    </button>
                </div>
            </div>
        </div>
    );
}

function MagazineStatusComponent() {
    const [magazineStatus, setMagazineStatus] = useState<MagazineStatus | null>(null);

    useEffect(() => {
        const fetchMagazineStatus = async () => {
            try {
                const res = await fetch(`${API_URL}/magazine-status`);
                if (res.ok) {
                    setMagazineStatus(await res.json());
                }
            } catch (error) {
                console.error("Failed to fetch magazine status:", error);
            }
        };

        fetchMagazineStatus();
        // Poll magazine status every 5 seconds
        const interval = setInterval(fetchMagazineStatus, 5000);
        return () => clearInterval(interval);
    }, []);

    if (!magazineStatus) return null;

    return (
        <div style={{display: 'flex', gap: 16, alignItems: 'center', justifyContent: 'center', marginBottom: 12}}>
            <div style={{display: 'flex', alignItems: 'center', gap: 8}}>
                {magazineStatus.magazine1_full ?
                    <img
                        src="/green_coins.png"
                        alt="Green coins magazine 1"
                        style={{width: 32, height: 32}}
                    />
                    : <img
                        src="/red_coins.png"
                        alt="Red coins magazine 1"
                        style={{width: 32, height: 32}}
                    />
                }
                {magazineStatus.magazine2_full ? <img
                        src="/green_coins.png"
                        alt="Green coins magazine 2"
                        style={{width: 32, height: 32}}
                    /> :
                    <img
                        src="/red_coins.png"
                        alt="Red coins magazine 2"
                        style={{width: 32, height: 32}}
                    />}
            </div>
        </div>
    );
}

export default function Home() {
    const [state, setState] = useState<BoardResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [setup, setSetup] = useState(true);
    const [difficulty, setDifficulty] = useState("impossible");
    const [whoStarts, setWhoStarts] = useState("player");
    const [trainingMode, setTrainingMode] = useState(false);
    const [screen, setScreen] = useState<'start' | 'game' | 'leaderboard'>('start');
    const [showErrorDialog, setShowErrorDialog] = useState(false);
    const [errorDialogMessage, setErrorDialogMessage] = useState('');
    const [nickname, setNickname] = useState<string>(() => {
        if (typeof window !== 'undefined') {
            return localStorage.getItem('nickname') || '';
        }
        return '';
    });

    // Persist nickname across sessions
    useEffect(() => {
        if (typeof window !== 'undefined') {
            localStorage.setItem('nickname', nickname);
        }
    }, [nickname]);

    // Start game only after setup
    const startGame = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(`${API_URL}/start`, {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({difficulty, who_starts: whoStarts, training_mode: trainingMode}),
            });

            if (!res.ok) {
                const errorData = await res.json().catch(() => ({ detail: "Failed to parse error response" }));
                if (res.status === 400 && errorData.detail && errorData.detail.includes('Magazine')) {
                    setErrorDialogMessage(errorData.detail);
                    setShowErrorDialog(true);
                } else {
                    setError(errorData.detail || "Failed to start game");
                }
                // Stop execution since the game failed to start
                return;
            }

            setState(await res.json());
            setSetup(false);
            setScreen('game');
        } catch (err) {
            setError("Could not connect to backend. Is the server running?");
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
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({column: col}),
            });

            if (!res.ok) {
                const errorData = await res.json().catch(() => ({ detail: "Failed to parse error response" }));
                if (res.status === 400 && errorData.detail && errorData.detail.includes('Magazine')) {
                    setErrorDialogMessage(errorData.detail);
                    setShowErrorDialog(true);
                }
                 else {
                    // For other errors, use the small inline error text
                    setError(errorData.detail || "Move failed");
                }
                return; // Stop execution after handling the error
            }

            setState(await res.json());
        } catch (e) {
            console.log('Move failed with exception:', e);
            setError("Move failed");
        } finally {
            setLoading(false);
        }
    };

    const reset = async () => {
        setLoading(true);
        setError(null);
        try {
            await fetch(`${API_URL}/reset`, {method: "POST"});
            setState(null);
            setSetup(true);
            setScreen('start');
        } catch {
            setError("Reset failed");
        } finally {
            setLoading(false);
        }
    };

    const closeErrorDialog = () => {
        setShowErrorDialog(false);
        setErrorDialogMessage('');
    };

    const goToLeaderboard = () => setScreen('leaderboard');
    const goToStart = () => setScreen('start');

    return (
        <div className={styles.page} style={{
            minHeight: 600,
            minWidth: 1024,
            width: 1024,
            height: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: '#1e293b',
            overflow: 'hidden',
            padding: 0
        }}>
            <div style={{
                width: 600,
                height: '95%',
                maxWidth: 600,
                maxHeight: '95vh',
                padding: 0,
                boxShadow: '0 4px 24px #0008',
                borderRadius: 20,
                background: '#22223b',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'flex-start',
                alignItems: 'center',
                overflow: 'hidden'
            }}>
                <MagazineStatusComponent/>
                <main className={styles.main} style={{
                    alignItems: 'center',
                    justifyContent: 'flex-start',
                    padding: 0,
                    width: '100%',
                    height: '100%',
                    overflow: 'hidden',
                    display: 'flex',
                    flexDirection: 'column'
                }}>
                    {screen === 'start' && (
                        <StartingScreen
                            difficulty={difficulty}
                            setDifficulty={setDifficulty}
                            whoStarts={whoStarts}
                            setWhoStarts={setWhoStarts}
                            trainingMode={trainingMode}
                            setTrainingMode={setTrainingMode}
                            startGame={startGame}
                            loading={loading}
                            error={error}
                            goToLeaderboard={goToLeaderboard}
                            nickname={nickname}
                            setNickname={setNickname}
                        />
                    )}
                    {screen === 'game' && state && state.board && (
                        <GameScreen
                            state={state}
                            loading={loading}
                            error={error}
                            makeMove={makeMove}
                            reset={reset}
                            trainingMode={trainingMode}
                            goToStart={goToStart}
                        />
                    )}
                    {screen === 'leaderboard' && (
                        <LeaderboardScreen goToStart={goToStart}/>
                    )}
                </main>
            </div>
            <ErrorDialog
                isOpen={showErrorDialog}
                message={errorDialogMessage}
                onClose={closeErrorDialog}
            />
        </div>
    );
}
