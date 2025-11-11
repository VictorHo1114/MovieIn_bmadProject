'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Api, type Top10Item } from '@/lib/api';
import { movieListStore } from '@/lib/movieListStore';
import { movieExistsCache } from '@/lib/movieExistsCache';

// 將 Top10Item 轉換為 MovieCard 需要的格式
function toRecommendedMovie(item: Top10Item) {
  return {
    id: item.movie.id.toString(),
    title: item.movie.title,
    overview: item.movie.overview,
    poster_url: item.movie.poster_url || '',
    vote_average: item.movie.vote_average,
    release_year: item.movie.release_year ?? undefined,
  };
}

// 可拖拽的 Top10 項目組件
interface SortableTop10ItemProps {
  item: Top10Item;
  index: number;
  onRemove: () => void;
}

function SortableTop10Item({ item, index, onRemove }: SortableTop10ItemProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: item.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`bg-white border-2 rounded-lg p-4 mb-3 ${
        isDragging ? 'border-purple-500 shadow-xl' : 'border-gray-200'
      }`}
    >
      <div className="flex items-center gap-4">
        {/* 排名徽章 */}
        <div className="flex-shrink-0">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-yellow-400 to-orange-500 flex items-center justify-center font-bold text-white text-lg shadow-lg">
            #{index + 1}
          </div>
        </div>

        {/* 電影海報 */}
        <div className="flex-shrink-0">
          <img
            src={item.movie.poster_url || '/placeholder-movie.png'}
            alt={item.movie.title}
            className="w-16 h-24 object-cover rounded shadow-md"
          />
        </div>

        {/* 電影資訊 */}
        <div className="flex-1 min-w-0">
          <h3 className="font-bold text-lg text-gray-900 truncate">
            {item.movie.title}
          </h3>
          {item.movie.release_year && (
            <p className="text-sm text-gray-500">{item.movie.release_year}</p>
          )}
          <div className="flex items-center gap-2 mt-1">
            <span className="text-yellow-500">★</span>
            <span className="text-sm font-medium text-gray-700">
              {item.movie.vote_average.toFixed(1)}
            </span>
          </div>
        </div>

        {/* 拖拽手柄 */}
        <div
          {...attributes}
          {...listeners}
          className="flex-shrink-0 cursor-grab active:cursor-grabbing p-2 hover:bg-gray-100 rounded transition-colors"
        >
          <svg
            className="w-6 h-6 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 8h16M4 16h16"
            />
          </svg>
        </div>

        {/* 刪除按鈕 */}
        <button
          onClick={onRemove}
          className="flex-shrink-0 p-2 text-red-500 hover:bg-red-50 rounded transition-colors"
          title="從 Top 10 移除"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>
    </div>
  );
}

export function Top10Section() {
  const [top10List, setTop10List] = useState<Top10Item[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  useEffect(() => {
    fetchTop10();
    
    // 訂閱 store 變化，使用本地過濾而非重新載入
    const unsubscribe = movieListStore.subscribe(() => {
      // 只更新本地狀態，過濾掉已移除的電影
      setTop10List(prevList => 
        prevList.filter(item => 
          movieListStore.isInTop10(item.movie.id)
        )
      );
    });
    
    return unsubscribe;
  }, []);

  const fetchTop10 = async () => {
    try {
      setIsLoading(true);
      const data = await Api.top10.getAll();
      // 按 rank 排序
      const sorted = data.items.sort((a, b) => a.rank - b.rank);
      setTop10List(sorted);
      
      // 🎯 優化：預先標記這些電影為存在於 DB
      const tmdbIds = data.items.map(item => item.movie.id);
      movieExistsCache.markAsExists(tmdbIds);
      
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch top10:', err);
      setError('載入 Top 10 清單失敗');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;

    if (!over || active.id === over.id) {
      return;
    }

    const oldIndex = top10List.findIndex((item) => item.id === active.id);
    const newIndex = top10List.findIndex((item) => item.id === over.id);

    const newList = arrayMove(top10List, oldIndex, newIndex);
    
    // 更新本地狀態（樂觀更新）
    setTop10List(newList);

    // 儲存到後端
    try {
      setIsSaving(true);
      const reorderData = newList.map((item: Top10Item, index: number) => ({
        id: item.id,
        rank: index + 1,
      }));
      await Api.top10.reorder(reorderData);
    } catch (err: any) {
      console.error('Failed to reorder top10:', err);
      alert('排序儲存失敗，請重試');
      // 恢復原始順序
      fetchTop10();
    } finally {
      setIsSaving(false);
    }
  };

  const handleRemove = async (item: Top10Item) => {
    if (!confirm(`確定要將「${item.movie.title}」從 Top 10 移除嗎？`)) {
      return;
    }

    try {
      await Api.top10.remove(item.tmdb_id);
      await fetchTop10();
    } catch (err: any) {
      console.error('Failed to remove from top10:', err);
      alert('移除失敗，請重試');
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col justify-center items-center py-20">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full"
        />
        <p className="text-gray-600 text-lg mt-4">載入中...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-20">
        <p className="text-red-600 mb-4">{error}</p>
        <button
          onClick={fetchTop10}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          重試
        </button>
      </div>
    );
  }

  if (top10List.length === 0) {
    return (
      <div className="text-center py-20">
        <div className="text-6xl mb-4 opacity-30">🏆</div>
        <p className="text-xl text-gray-600 mb-2">你的 Top 10 清單是空的</p>
        <p className="text-sm text-gray-400">
          點擊電影卡片的「加入 Top 10 List」按鈕來新增電影（最多 10 部）
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            我的 Top 10 <span className="text-yellow-600">({top10List.length}/10)</span>
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            拖曳電影來調整排名順序
          </p>
        </div>
        {isSaving && (
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full"
            />
            儲存中...
          </div>
        )}
      </div>

      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext
          items={top10List.map((item) => item.id)}
          strategy={verticalListSortingStrategy}
        >
          {top10List.map((item, index) => (
            <SortableTop10Item
              key={item.id}
              item={item}
              index={index}
              onRemove={() => handleRemove(item)}
            />
          ))}
        </SortableContext>
      </DndContext>
    </div>
  );
}
