"use client";

import { useState, useEffect } from "react";
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

const Camera = () => {
	const [state, setState] = useState<BoardResponse | null>(null);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const [setup, setSetup] = useState(true);
	const [difficulty, setDifficulty] = useState("impossible");
	const [whoStarts, setWhoStarts] = useState("player");
	const [trainingMode, setTrainingMode] = useState(false);

	useEffect(() => {
		const ws = new WebSocket("ws://localhost:8000/ws/camera");

		ws.binaryType = "arraybuffer";

		ws.onmessage = (event) => {
			const blob = new Blob([event.data], { type: "image/jpeg" });
			const url = URL.createObjectURL(blob);
			const img = document.getElementById("camera") as HTMLImageElement;
			if (img) img.src = url;
		};

		return () => ws.close();
	}, []);

	return (
		<main className="p-4">
			<h1 className="text-2xl font-bold">Settings</h1>
			<p className="mt-2">Configure your Connect 4 game here.</p>
			<img id="camera" width="640" height="480" />
		</main>
	);
}

export default Camera
