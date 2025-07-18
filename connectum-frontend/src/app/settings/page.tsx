"use client";

import { useEffect, useRef, useState } from "react";

const GRID_ROWS = 6;
const GRID_COLS = 7;
const GRID_CELL_SIZE = 40;
const GRID_WIDTH = GRID_COLS * GRID_CELL_SIZE;
const GRID_HEIGHT = GRID_ROWS * GRID_CELL_SIZE;

const API_URL = "http://localhost:8000"; // Change if backend runs elsewhere

export default function DebugDashboard() {
	const [grid, setGrid] = useState(
		Array.from({ length: GRID_ROWS }, () => Array(GRID_COLS).fill(0))
	);
	const [checkboxes, setCheckboxes] = useState<Record<string, boolean>>({});
	const [image, setImage] = useState<string | null>(null);
	const [currentImageIndex, setCurrentImageIndex] = useState(0);
	const canvasRef = useRef<HTMLCanvasElement | null>(null);
	const wsRef = useRef<WebSocket | null>(null);

	const [currentIndex, setCurrentIndex] = useState(0);

	useEffect(() => {
		const canvas = canvasRef.current;
		if (!canvas) return;
		const ctx = canvas.getContext("2d");
		if (!ctx) return;

		ctx.clearRect(0, 0, canvas.width, canvas.height);

		for (let i = 0; i < GRID_ROWS; i++) {
			for (let j = 0; j < GRID_COLS; j++) {
				const cx = j * GRID_CELL_SIZE + GRID_CELL_SIZE / 2;
				const cy = i * GRID_CELL_SIZE + GRID_CELL_SIZE / 2;
				const radius = GRID_CELL_SIZE / 2 - 4;
				const val = grid[i][j];

				if (val === -1) ctx.fillStyle = "red";
				else if (val === 1) ctx.fillStyle = "yellow";
				else continue;

				ctx.beginPath();
				ctx.arc(cx, cy, radius, 0, 2 * Math.PI);
				ctx.fill();
				ctx.strokeStyle = "black";
				ctx.lineWidth = 2;
				ctx.stroke();
			}
		}
	}, [grid]);

	useEffect(() => {
		fetch(`${API_URL}/options_list`)
			.then((res) => res.json())
			.then((data) => setCheckboxes(data))
			.catch((err) => console.error("Failed to fetch options", err));
	}, []);

	useEffect(() => {
		const ws = new WebSocket("ws://localhost:8000/ws/camera");
		ws.binaryType = "blob";
		wsRef.current = ws;

		ws.onopen = () => {
			console.log("WebSocket connected");
			ws.send(JSON.stringify({ carousel_index: currentIndex }));
		};

		ws.onmessage = (event) => {
			if (event.data instanceof Blob) {
				const blobUrl = URL.createObjectURL(event.data);
				setImage(blobUrl);
			}
		};

		ws.onerror = (err) => {
			console.error("WebSocket error", err);
		};

		ws.onclose = () => {
			console.log("WebSocket disconnected");
		};

		return () => {
			ws.close();
		};
	}, [currentImageIndex]);

	// Handle carousel movement
	const handlePrev = () => {
		const newIndex = (currentIndex - 1 + 5) % 5;
		setCurrentIndex(newIndex);
		sendIndex(newIndex);
	};

	const handleNext = () => {
		const newIndex = (currentIndex + 1) % 5;
		setCurrentIndex(newIndex);
		sendIndex(newIndex);
	};

	const sendIndex = (index: number) => {
		if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
			wsRef.current.send(JSON.stringify({ carousel_index: index }));
		}
	};

	const toggleCheckbox = async (key: string) => {
		const newValue = !checkboxes[key];
		setCheckboxes((prev) => ({ ...prev, [key]: newValue }));

		try {
			await fetch(`${API_URL}/option`, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ label: key, value: newValue })
			});
		} catch (error) {
			console.error("Failed to update option", error);
		}
	};

	return (
		<main className="flex p-4">
			<div className="flex flex-col items-center">
				<div className="w-[320px] h-[240px] bg-gray-100 border flex items-center justify-center">
					{image ? (
						<img src={image} alt={`Image ${currentIndex}`} className="w-full h-full object-contain" />
					) : (
						<span>Loading image...</span>
					)}
				</div>
				<div className="flex gap-4 mt-4">
					<button onClick={handlePrev} className="px-3 py-1 bg-blue-500 text-white rounded">Prev</button>
					<span>Image {currentIndex + 1} / 5</span>
					<button onClick={handleNext} className="px-3 py-1 bg-blue-500 text-white rounded">Next</button>
				</div>
			</div>

			<div className="ml-8 space-y-6">
				<div>
					<h2 className="text-xl font-bold mb-2">Camera Options</h2>
					{Object.keys(checkboxes).map((opt) => (
						<div key={opt} className="flex items-center space-x-2">
							<button
								className={`px-2 py-1 border rounded ${checkboxes[opt] ? "bg-blue-500 text-white" : "bg-white text-black"}`}
								onClick={() => toggleCheckbox(opt)}
							>
								{opt
									.replace(/_/g, " ")
									.toLowerCase()
									.replace(/\b\w/g, (c) => c.toUpperCase())}
							</button>
						</div>
					))}
				</div>
			</div>
		</main>
	);
}
