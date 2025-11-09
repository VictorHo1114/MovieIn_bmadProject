"use client";

import { useEffect, useRef, useCallback } from "react";

interface BlackHoleCanvasProps {
  onGenerate: () => void;
  isLoading: boolean;
}

export function BlackHoleCanvas({ onGenerate, isLoading }: BlackHoleCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const animationFrameRef = useRef<number | undefined>(undefined);
  const starsRef = useRef<any[]>([]);

  useEffect(() => {
    if (!containerRef.current || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const h = 600;
    const w = 600;
    const cw = w;
    const ch = h;
    const maxorbit = 300;
    const centery = ch / 2;
    const centerx = cw / 2;

    const startTime = performance.now(); // 使用 performance.now() 更精確
    let currentTime = 0;

    canvas.width = cw;
    canvas.height = ch;
    const context = canvas.getContext("2d", { 
      alpha: false, // 禁用透明度以提升性能
      desynchronized: true // 允許異步渲染
    });
    if (!context) return;

    // 移除這行，它會降低性能
    // context.globalCompositeOperation = "multiply";

    function setDPI(canvas: HTMLCanvasElement, dpi: number) {
      if (!canvas.style.width) canvas.style.width = canvas.width + "px";
      if (!canvas.style.height) canvas.style.height = canvas.height + "px";

      const scaleFactor = dpi / 96;
      canvas.width = Math.ceil(canvas.width * scaleFactor);
      canvas.height = Math.ceil(canvas.height * scaleFactor);
      const ctx = canvas.getContext("2d");
      ctx?.scale(scaleFactor, scaleFactor);
    }

    function rotate(cx: number, cy: number, x: number, y: number, angle: number) {
      const radians = angle;
      const cos = Math.cos(radians);
      const sin = Math.sin(radians);
      const nx = cos * (x - cx) + sin * (y - cy) + cx;
      const ny = cos * (y - cy) - sin * (x - cx) + cy;
      return [nx, ny];
    }

    setDPI(canvas, 192);

    class Star {
      orbital: number;
      x: number;
      y: number;
      yOrigin: number;
      speed: number;
      rotation: number;
      startRotation: number;
      id: number;
      collapseBonus: number;
      color: string;
      hoverPos: number;
      expansePos: number;
      prevR: number;
      prevX: number;
      prevY: number;
      originalY: number;

      constructor() {
        const rands = [];
        rands.push(Math.random() * (maxorbit / 2) + 1);
        rands.push(Math.random() * (maxorbit / 2) + maxorbit);

        this.orbital = rands.reduce((p, c) => p + c, 0) / rands.length;

        this.x = centerx;
        this.y = centery + this.orbital;
        this.yOrigin = centery + this.orbital;

        this.speed = (Math.floor(Math.random() * 2.5) + 1.5) * (Math.PI / 180);
        this.rotation = 0;
        this.startRotation = (Math.floor(Math.random() * 360) + 1) * (Math.PI / 180);

        this.id = starsRef.current.length;

        this.collapseBonus = this.orbital - maxorbit * 0.7;
        if (this.collapseBonus < 0) {
          this.collapseBonus = 0;
        }

        this.color = "rgba(255,255,255," + (1 - this.orbital / 255) + ")";

        this.hoverPos = centery + maxorbit / 2 + this.collapseBonus;
        this.expansePos = centery + ((this.id % 100) * -10 + (Math.floor(Math.random() * 20) + 1));

        this.prevR = this.startRotation;
        this.prevX = this.x;
        this.prevY = this.y;
        this.originalY = this.yOrigin;

        starsRef.current.push(this);
      }

      draw() {
        if (!context) return;

        this.rotation = this.startRotation + currentTime * this.speed;

        context.save();
        context.fillStyle = this.color;
        context.strokeStyle = this.color;
        context.beginPath();
        const oldPos = rotate(centerx, centery, this.prevX, this.prevY, -this.prevR);
        context.moveTo(oldPos[0], oldPos[1]);
        context.translate(centerx, centery);
        context.rotate(this.rotation);
        context.translate(-centerx, -centery);
        context.lineTo(this.x, this.y);
        context.stroke();
        context.restore();

        this.prevR = this.rotation;
        this.prevX = this.x;
        this.prevY = this.y;
      }
    }

    function loop() {
      if (!context) return;
      const now = performance.now(); // 使用 performance.now()
      currentTime = (now - startTime) / 50;

      context.fillStyle = "rgba(0,0,0,0.2)";
      context.fillRect(0, 0, cw, ch);

      // 批量繪製以提升性能
      const stars = starsRef.current;
      for (let i = 0; i < stars.length; i++) {
        if (stars[i] !== undefined) {
          stars[i].draw();
        }
      }

      animationFrameRef.current = requestAnimationFrame(loop);
    }

    function init() {
      if (!context) return;
      context.fillStyle = "rgba(0,0,0,1)";
      context.fillRect(0, 0, cw, ch);
      
      // 減少星星數量從 2500 到 1500 以提升性能
      for (let i = 0; i < 1500; i++) {
        new Star();
      }
      loop();
    }

    init();

    // 清理函數
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      starsRef.current = [];
    };
  }, []);

  return (
    <div ref={containerRef} className="relative w-[600px] h-[600px]">
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full" />

      <button
        onClick={onGenerate}
        disabled={isLoading}
        className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-10
                   w-32 h-32 rounded-full
                   bg-gradient-to-br from-white/90 to-gray-300/90
                   hover:from-white hover:to-gray-200
                   text-black font-bold text-base
                   border-4 border-white
                   shadow-[0_0_30px_rgba(255,255,255,0.8),0_0_60px_rgba(255,255,255,0.4)]
                   hover:shadow-[0_0_40px_rgba(255,255,255,1),0_0_80px_rgba(255,255,255,0.6)]
                   transition-all duration-300
                   hover:scale-110
                   disabled:opacity-50 disabled:cursor-not-allowed
                   backdrop-blur-sm
                   flex items-center justify-center
                   will-change-transform"
      >
        <span className="drop-shadow-lg">{isLoading ? "生成中..." : "GENERATE"}</span>
      </button>
    </div>
  );
}
