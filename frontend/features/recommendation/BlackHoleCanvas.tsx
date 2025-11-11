"use client";

import { useEffect, useRef, useCallback, useState } from "react";

interface BlackHoleCanvasProps {
  onGenerate: () => void;
  isLoading: boolean;
}

export function BlackHoleCanvas({ onGenerate, isLoading }: BlackHoleCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const animationFrameRef = useRef<number | undefined>(undefined);
  const starsRef = useRef<any[]>([]);
  
  // 響應式尺寸狀態
  const [canvasSize, setCanvasSize] = useState({
    width: typeof window !== 'undefined' && window.innerWidth < 640 ? 350 : 700,
    height: typeof window !== 'undefined' && window.innerWidth < 640 ? 350 : 700,
  });

  // 監聽視窗大小變化
  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth;
      let size = 700; // Desktop default
      
      if (width < 480) {
        size = 300; // 超小手機
      } else if (width < 640) {
        size = 350; // 手機
      } else if (width < 1024) {
        size = 500; // 平板
      }
      
      setCanvasSize({ width: size, height: size });
    };

    handleResize(); // 初始化
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    if (!containerRef.current || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const h = canvasSize.height;
    const w = canvasSize.width;
    const cw = w;
    const ch = h;
    const maxorbit = (w / 700) * 250; // 根據 canvas 大小縮放軌道
    const centery = ch / 2;
    const centerx = cw / 2;

    const startTime = performance.now(); // 使用 performance.now() 更精確
    let currentTime = 0;

    canvas.width = cw;
    canvas.height = ch;
    const context = canvas.getContext("2d", { 
      alpha: true, // 啟用透明度
      desynchronized: true // 允許異步渲染
    });
    if (!context) return;

    // 移除這行，它會降低性能
    // context.globalCompositeOperation = "multiply";

    function setDPI(canvas: HTMLCanvasElement, dpi: number) {
      // 保存原始邏輯尺寸
      const logicalWidth = cw;
      const logicalHeight = ch;
      
      const scaleFactor = dpi / 96;
      canvas.width = Math.ceil(logicalWidth * scaleFactor);
      canvas.height = Math.ceil(logicalHeight * scaleFactor);
      
      // 設定 CSS 尺寸為邏輯尺寸
      canvas.style.width = logicalWidth + "px";
      canvas.style.height = logicalHeight + "px";
      
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

        // 根據軌道大小調整透明度（使用 maxorbit 而不是固定值 255）
        this.color = "rgba(255,255,255," + (1 - this.orbital / (maxorbit * 1.5)) + ")";

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
      const now = performance.now();
      currentTime = (now - startTime) / 50;

      // 不使用fillRect清除，而是讓舊的星星自然淡出
      // 使用globalCompositeOperation來控制混合模式
      context.globalCompositeOperation = "destination-out";
      context.fillStyle = "rgba(0, 0, 0, 0.1)"; // 淡出舊內容
      context.fillRect(0, 0, cw, ch);
      context.globalCompositeOperation = "source-over"; // 恢復正常繪製

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
      // 完全透明的初始背景
      context.clearRect(0, 0, cw, ch);
      
      // 根據 canvas 大小調整星星數量
      const starCount = Math.floor((w / 700) * 1200);
      
      for (let i = 0; i < starCount; i++) {
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
  }, [canvasSize]); // 依賴 canvasSize，尺寸改變時重新初始化

  return (
    <div 
      ref={containerRef} 
      className="relative flex items-center justify-center"
      style={{
        width: `${canvasSize.width}px`,
        height: `${canvasSize.height}px`,
      }}
    >
      <canvas 
        ref={canvasRef} 
        className="absolute inset-0" 
        style={{
          width: `${canvasSize.width}px`,
          height: `${canvasSize.height}px`,
        }}
      />

      <button
        onClick={onGenerate}
        disabled={isLoading}
        className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-10
                   w-16 h-16 xs:w-20 xs:h-20 sm:w-24 sm:h-24 md:w-32 md:h-32
                   rounded-full
                   bg-gradient-to-br from-white/90 to-gray-300/90
                   hover:from-white hover:to-gray-200
                   text-black font-bold text-[10px] xs:text-xs sm:text-sm md:text-base
                   border-2 sm:border-3 md:border-4 border-white
                   shadow-[0_0_15px_rgba(255,255,255,0.5),0_0_30px_rgba(255,255,255,0.25)]
                   xs:shadow-[0_0_20px_rgba(255,255,255,0.6),0_0_40px_rgba(255,255,255,0.3)]
                   sm:shadow-[0_0_25px_rgba(255,255,255,0.7),0_0_50px_rgba(255,255,255,0.35)]
                   md:shadow-[0_0_30px_rgba(255,255,255,0.8),0_0_60px_rgba(255,255,255,0.4)]
                   hover:shadow-[0_0_40px_rgba(255,255,255,1),0_0_80px_rgba(255,255,255,0.6)]
                   transition-all duration-300
                   hover:scale-110
                   active:scale-95
                   disabled:opacity-50 disabled:cursor-not-allowed
                   backdrop-blur-sm
                   flex items-center justify-center
                   will-change-transform"
      >
        <span className="drop-shadow-lg whitespace-nowrap px-1 xs:px-2">
          {isLoading ? "生成中..." : "GENERATE"}
        </span>
      </button>
    </div>
  );
}
