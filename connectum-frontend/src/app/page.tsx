"use client";

import {useState, useEffect} from "react";
import styles from "./page.module.css";
import yourTurnMessages from './yourTurnMessages.json';

interface BoardResponse {
    board: number[][];
    winner: number | null;
    turn: number;
    valid_moves: number[];
    scores?: number[];
    final_score?: number;
    move_message?: string;
}

interface MagazineStatus {
    magazine_1_empty: boolean;
    magazine_2_empty: boolean;
}

const API_URL = "http://localhost:8000"; // Change if backend runs elsewhere
const WS_URL = API_URL.replace(/^http/, 'ws');

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
            <div style={{width: '100%', display: 'flex', alignItems: 'center', gap: 8}}>
                <input type="checkbox" id="trainingMode" checked={trainingMode}
                       onChange={e => setTrainingMode(e.target.checked)} style={{width: 20, height: 20, cursor: 'pointer'}}/>
                <label htmlFor="trainingMode" style={{fontWeight: 600, fontSize: 18, color: '#f8fafc', cursor: 'pointer'}}>Training
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
                        nickname,
                        goToLeaderboard,
                    }: {
    state: BoardResponse;
    loading: boolean;
    error: string | null;
    makeMove: (col: number) => void;
    reset: () => void;
    trainingMode: boolean;
    goToStart: () => void;
    nickname: string;
    goToLeaderboard: () => void;
}) {
    const [showMoveMessage, setShowMoveMessage] = useState(false);
    const [currentYourTurnMessage, setCurrentYourTurnMessage] = useState('');

    // Handle move message timer
    useEffect(() => {
        if (state.move_message && state.turn === 0) {
            setShowMoveMessage(true);

            // Clear the move message after 6 seconds and show "Your Turn" message
            const timer = setTimeout(() => {
                setShowMoveMessage(false);
                // Pick a random "Your Turn" message
                const randomMessage = yourTurnMessages[Math.floor(Math.random() * yourTurnMessages.length)];
                setCurrentYourTurnMessage(randomMessage);
            }, 6000);

            return () => clearTimeout(timer);
        } else if (state.turn === 0 && !state.move_message) {
            // If it's player's turn but no move message, show random "Your Turn" message immediately
            const randomMessage = yourTurnMessages[Math.floor(Math.random() * yourTurnMessages.length)];
            setCurrentYourTurnMessage(randomMessage);
        }
    }, [state.move_message, state.turn]);

    // Reset messages when it's not player's turn
    useEffect(() => {
        if (state.turn !== 0) {
            setShowMoveMessage(false);
            setCurrentYourTurnMessage('');
        }
    }, [state.turn]);

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

            {state.winner !== null ? (
                <div style={{
                    width: '100%',
                    color: '#f8fafc',
                    fontSize: 20,
                    fontWeight: 700,
                    textAlign: 'center',
                    marginBottom: 12,
                    padding: '12px',
                    background: '#232946',
                    borderRadius: 10,
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    gap: 16
                }}>
                    <div>
                        <b>Winner:</b> {state.winner === -1 ? "Player" : state.winner === 1 ? "Bot" : state.winner === 0 ? "Draw" : ""}
                    </div>
                    {state.final_score !== undefined && (
                        <div>Your Score: {state.final_score}</div>
                    )}
                </div>
            ) : (
                <div style={{
                    marginBottom: 2,
                    marginTop: 2,
                    fontSize: 18,
                    minHeight: 48,
                    color: '#f8fafc',
                    fontWeight: 600,
                    textAlign: 'center',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '8px 16px'
                }}>
                    {state.turn === 0 ? (
                        // Show move message for 6 seconds, then show random "Your Turn" message
                        showMoveMessage && state.move_message ? (
                            <div style={{
                                fontStyle: 'italic',
                                fontSize: 16,
                                lineHeight: '1.4',
                                maxWidth: '400px',
                                fontWeight: 400
                            }}>
                                {state.move_message}
                            </div>
                        ) : currentYourTurnMessage ? (
                            <div style={{
                                fontSize: 16,
                                lineHeight: '1.4',
                                maxWidth: '400px',
                                fontWeight: 500,
                                color: '#38bdf8'
                            }}>
                                {currentYourTurnMessage}
                            </div>
                        ) : "Your turn"
                    ) : "Bot's turn"}
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
                {state.board.slice().reverse().map((row, rowIdx) =>
                    row.map((cell, colIdx) => (
                        <button
                            key={`${state.board.length - 1 - rowIdx}-${colIdx}`}
                            style={{
                                width: 48,
                                height: 48,
                                borderRadius: "50%",
                                background: cell === 0 ? "#e0e7ef" : cell === 1 ? "#f43f5e" : "#facc15",
                                border: (state.valid_moves.includes(colIdx) && state.turn === 0 && state.winner === null) ? "2px solid #38bdf8" : "1px solid #64748b",
                                cursor: (state.valid_moves.includes(colIdx) && !loading && state.winner === null && state.turn === 0) ? "pointer" : "default",
                                boxShadow: cell !== 0 ? '0 2px 8px #0002' : undefined,
                                fontSize: 14,
                                fontWeight: 700,
                                color: cell === 1 ? '#fff' : cell === -1 ? '#222' : '#222',
                                outline: 'none',
                                transition: 'background 0.2s, border 0.2s',
                                margin: 0,
                                padding: 0,
                            }}
                            disabled={loading || !state.valid_moves.includes(colIdx) || state.winner !== null || state.turn !== 0}
                            onClick={() => makeMove(colIdx)}
                            aria-label={`Drop in column ${colIdx + 1}`}
                        />
                    ))
                )}
            </div>

            {/* Training Mode Score Display */}
            {trainingMode && state.scores && (
                <div style={{
                    display: "grid",
                    gridTemplateColumns: `repeat(${state.board[0].length}, 48px)`,
                    gap: 2,
                    margin: '4px auto 0 auto',
                    justifyContent: 'center',
                }}>
                    {state.scores.map((score, colIdx) => (
                        <div
                            key={colIdx}
                            style={{
                                width: 48,
                                height: 24,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontSize: 12,
                                fontWeight: 600,
                                color: state.valid_moves.includes(colIdx) ? '#f8fafc' : '#64748b',
                                background: state.valid_moves.includes(colIdx) ? '#1e40af' : '#334155',
                                borderRadius: 4,
                                border: '1px solid #475569'
                            }}
                        >
                            {state.valid_moves.includes(colIdx) ? score.toFixed(1) : '-'}
                        </div>
                    ))}
                </div>
            )}

            {state.winner !== null ? (
                <div style={{display: 'flex', gap: 8, width: '100%', marginTop: 8}}>
                    <button onClick={reset} disabled={loading} style={{
                        flex: 1,
                        fontSize: 16,
                        padding: '8px 0',
                        borderRadius: 8,
                        background: '#f59e42',
                        color: '#fff',
                        border: 'none',
                        fontWeight: 700,
                        cursor: loading ? 'not-allowed' : 'pointer',
                        opacity: loading ? 0.7 : 1,
                        boxShadow: '0 2px 8px #0004'
                    }}>New Game
                    </button>
                    <button onClick={goToLeaderboard} style={{
                        flex: 1,
                        fontSize: 16,
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
            ) : (
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
            )}
        </>
    );
}

function LeaderboardScreen({goToStart, currentPlayer}: { goToStart: () => void, currentPlayer: string }) {
    const [selectedDifficulty, setSelectedDifficulty] = useState('impossible');
    const [leaderboard, setLeaderboard] = useState<{
        difficulty: string,
        top_10: {nickname: string, score: number}[],
        current_player?: {rank: number, nickname: string, score: number},
        available_difficulties: string[]
    } | null>(null);
    const [loading, setLoading] = useState(true);

    const fetchLeaderboard = async (difficulty: string) => {
        setLoading(true);
        try {
            const response = await fetch(`${API_URL}/leaderboard?difficulty=${encodeURIComponent(difficulty)}&current_player=${encodeURIComponent(currentPlayer)}`);
            if (response.ok) {
                const data = await response.json();
                setLeaderboard(data);
            }
        } catch (error) {
            console.error('Failed to fetch leaderboard:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchLeaderboard(selectedDifficulty);
    }, [selectedDifficulty, currentPlayer]);

    const handleDifficultyChange = (difficulty: string) => {
        setSelectedDifficulty(difficulty);
    };

    return (
        <div style={{width: '100%', textAlign: 'center', color: '#f8fafc'}}>
            <h1 style={{
                fontSize: 28,
                fontWeight: 700,
                margin: '8px 0 16px 0',
                textAlign: 'center',
                letterSpacing: 2
            }}>Leaderboard</h1>

            {/* Difficulty Selector */}
            <div style={{marginBottom: 20}}>
                <div style={{
                    display: 'flex',
                    justifyContent: 'center',
                    gap: 8,
                    flexWrap: 'wrap'
                }}>
                    {['easy', 'medium', 'hard', 'impossible'].map((difficulty) => (
                        <button
                            key={difficulty}
                            onClick={() => handleDifficultyChange(difficulty)}
                            style={{
                                padding: '8px 16px',
                                borderRadius: 8,
                                border: 'none',
                                fontWeight: 600,
                                cursor: 'pointer',
                                textTransform: 'capitalize',
                                backgroundColor: selectedDifficulty === difficulty ? '#3b82f6' : '#475569',
                                color: '#f8fafc',
                                transition: 'background-color 0.2s'
                            }}
                        >
                            {difficulty}
                        </button>
                    ))}
                </div>
            </div>

            {loading ? (
                <div style={{fontSize: 18, margin: '32px 0'}}>Loading...</div>
            ) : !leaderboard || leaderboard.top_10.length === 0 ? (
                <div style={{fontSize: 18, margin: '32px 0'}}>No scores yet for {selectedDifficulty} difficulty!</div>
            ) : (
                <>
                    <div style={{
                        width: '90%',
                        margin: '0 auto',
                        background: '#232946',
                        borderRadius: 10,
                        overflow: 'hidden'
                    }}>
                        <div style={{
                            display: 'grid',
                            gridTemplateColumns: '60px 1fr 100px',
                            gap: 16,
                            padding: '16px',
                            fontWeight: 700,
                            fontSize: 16,
                            borderBottom: '1px solid #475569'
                        }}>
                            <div>Rank</div>
                            <div>Name</div>
                            <div>Score</div>
                        </div>
                        {leaderboard.top_10.map((entry, idx) => (
                            <div key={idx} style={{
                                display: 'grid',
                                gridTemplateColumns: '60px 1fr 100px',
                                gap: 16,
                                padding: '12px 16px',
                                fontSize: 16,
                                borderBottom: idx < leaderboard.top_10.length - 1 ? '1px solid #334155' : 'none',
                                backgroundColor: entry.nickname === currentPlayer ? '#1e40af20' : 'transparent'
                            }}>
                                <div style={{fontWeight: 600}}>#{idx + 1}</div>
                                <div style={{textAlign: 'left'}}>{entry.nickname}</div>
                                <div style={{fontWeight: 600}}>{entry.score}</div>
                            </div>
                        ))}
                    </div>

                    {leaderboard.current_player && (
                        <>
                            <div style={{
                                margin: '16px 0 8px 0',
                                fontSize: 16,
                                color: '#cbd5e1'
                            }}>
                                Your Ranking in {selectedDifficulty}:
                            </div>
                            <div style={{
                                width: '90%',
                                margin: '0 auto',
                                background: '#1e40af',
                                borderRadius: 10,
                                overflow: 'hidden'
                            }}>
                                <div style={{
                                    display: 'grid',
                                    gridTemplateColumns: '60px 1fr 100px',
                                    gap: 16,
                                    padding: '12px 16px',
                                    fontSize: 16,
                                    fontWeight: 600
                                }}>
                                    <div>#{leaderboard.current_player.rank}</div>
                                    <div style={{textAlign: 'left'}}>{leaderboard.current_player.nickname}</div>
                                    <div>{leaderboard.current_player.score}</div>
                                </div>
                            </div>
                        </>
                    )}
                </>
            )}

            <button onClick={goToStart} style={{
                width: '80%',
                fontSize: 16,
                marginTop: 24,
                padding: '12px 0',
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
    const [wsConnected, setWsConnected] = useState(false);
    const [reconnectAttempts, setReconnectAttempts] = useState(0);

    useEffect(() => {
        let reconnectTimer: NodeJS.Timeout;
        let ws: WebSocket | null = null;

        const connectWebSocket = () => {
            try {
                ws = new WebSocket(`ws://localhost:8000/ws/magazine_status`);

                ws.onopen = () => {
                    console.log("Magazine status WebSocket connected");
                    setWsConnected(true);
                    setReconnectAttempts(0);
                };

                ws.onmessage = (event) => {
                    try {
                        const status = JSON.parse(event.data);
                        setMagazineStatus(status);
                    } catch (error) {
                        console.error("Failed to parse magazine status:", error);
                    }
                };

                ws.onclose = (event) => {
                    console.log("Magazine status WebSocket disconnected", event.code, event.reason);
                    setWsConnected(false);

                    // Only attempt to reconnect if it wasn't a manual close
                    if (event.code !== 1000) {
                        setReconnectAttempts(prev => prev + 1);
                        // Exponential backoff with max 10 seconds
                        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 10000);
                        console.log(`Attempting to reconnect in ${delay}ms...`);
                        reconnectTimer = setTimeout(connectWebSocket, delay);
                    }
                };

                ws.onerror = (error) => {
                    console.error("Magazine status WebSocket error:", error);
                    setWsConnected(false);
                };
            } catch (error) {
                console.error("Failed to create WebSocket:", error);
                setWsConnected(false);
                // Retry after 5 seconds if WebSocket creation fails
                reconnectTimer = setTimeout(connectWebSocket, 5000);
            }
        };

        // Only connect if we're in a browser environment
        if (typeof window !== 'undefined') {
            connectWebSocket();
        }

        return () => {
            if (reconnectTimer) {
                clearTimeout(reconnectTimer);
            }
            if (ws) {
                ws.close(1000, 'Component unmounting');
            }
        };
    }, [reconnectAttempts]);

    // Don't render anything if we don't have status yet
    if (!magazineStatus && !wsConnected) {
        return (
            <div style={{
                display: 'flex',
                gap: 8,
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: 12,
                color: '#64748b',
                fontSize: 12
            }}>
                Connecting to system...
            </div>
        );
    }

    return (
        <div style={{display: 'flex', gap: 16, alignItems: 'center', justifyContent: 'center', marginBottom: 12}}>
            <div style={{display: 'flex', alignItems: 'center', gap: 8}}>
                {magazineStatus?.magazine_1_empty === false ?
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
                {magazineStatus?.magazine_2_empty === false ? <img
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
            {!wsConnected && (
                <div style={{
                    fontSize: 12,
                    color: '#ef4444',
                    marginLeft: 8
                }}>
                    System offline
                </div>
            )}
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

    // WebSocket connection for live game state updates
    useEffect(() => {
        if (screen !== 'game') {
            return;
        }

        const ws = new WebSocket(`${WS_URL}/ws/game_state`);

        ws.onopen = () => {
            console.log("Game state WebSocket connected");
            setError(null); // Clear connection errors on successful connect
        };

        ws.onmessage = (event) => {
            try {
                const newState = JSON.parse(event.data);
                setState(newState);
            } catch (error) {
                console.error("Failed to parse game state from WebSocket:", error);
            }
        };

        ws.onclose = () => {
            console.log("Game state WebSocket disconnected");
        };

        ws.onerror = (error) => {
            console.error("Game state WebSocket error:", error);
            setError("Connection to game server lost. Please reset.");
        };

        // Cleanup on component unmount or screen change
        return () => {
            if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
                ws.close();
            }
        };
    }, [screen]);

    // Start game only after setup
    const startGame = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(`${API_URL}/new_game`, {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({
                    difficulty,
                    who_starts: whoStarts,
                    training_mode: trainingMode,
                    nickname: nickname.trim(),
                    no_camera: true, // Assuming debug mode from GUI
                    no_motors: true  // Assuming debug mode from GUI
                }),
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
                setLoading(false);
                return;
            }

            // Game started, now fetch initial state
            try {
                const statusRes = await fetch(`${API_URL}/status`);
                if (statusRes.ok) {
                    const initialState = await statusRes.json();
                    setState(initialState);
                    setSetup(false);
                    setScreen('game');
                } else {
                     setError("Failed to fetch initial game state.");
                }
            } catch (e) {
                setError("Could not connect to backend to get game state.");
            } finally {
                setLoading(false);
            }

        } catch (err) {
            setError("Could not connect to backend. Is the server running?");
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
                            nickname={nickname}
                            goToLeaderboard={goToLeaderboard}
                        />
                    )}
                    {screen === 'leaderboard' && (
                        <LeaderboardScreen goToStart={goToStart} currentPlayer={nickname.trim()}/>
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
