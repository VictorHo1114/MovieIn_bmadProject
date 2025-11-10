'use client'; 

import React from 'react';
import "slick-carousel/slick/slick.css";
import "slick-carousel/slick/slick-theme.css";
import Slider from 'react-slick'; 
import Link from 'next/link';
import { FaHeart, FaCalendarAlt, FaEye } from 'react-icons/fa'; 

// 這是 react-slick 需要的設定
const sliderSettings = {
  dots: true,
  infinite: true,
  speed: 500,
  slidesToShow: 1,
  slidesToScroll: 1,
  autoplay: true,
  arrows: true, // [修改！] false -> true，開啟箭頭 (你的需求 #2)
};

// (我們刪除了 collectionsSliderSettings)

export function HomeFeed() {
  
  return (
    <div className="container-fluid mx-auto px-4 py-4">
      
      {/* --- 1. 頂部輪播 (Slick Slider) --- */}
      {/* [修改！] 加上 px-10 relative 來為箭頭騰出空間 */}
      <div className="w-full mb-4 px-10 relative">
        <Slider {...sliderSettings}>
          {/* (我們假設圖片在 public/img/ 裡面) */}
          <div>
            <img src="/img/slider1.jpg" className="img-fluid rounded w-full" alt="Slider 1" />
          </div>
          <div>
            <img src="/img/slider2.jpg" className="img-fluid rounded w-full" alt="Slider 2" />
          </div>
          <div>
            <img src="/img/slider3.jpg" className="img-fluid rounded w-full" alt="Slider 3" />
          </div>
        </Slider>
      </div>

      {/* --- 2. "Movies" 標題列 (保持不變) --- */}
      <div className="flex items-center justify-between mt-4 mb-3">
        <h1 className="text-xl font-bold text-gray-900">Movies</h1>
        <Link href="/movies" className="text-xs text-gray-700 hidden sm:inline-block">
          View All <FaEye className="inline-block ml-1" />
        </Link>
      </div>

      {/* --- 3. "Movies" 內容卡片 (保持不變) --- */}
      <div className="flex flex-wrap -mx-2">
        
        {/* 卡片 1 (重複結構) */}
        <div className="w-full xl:w-1/4 md:w-1/2 mb-4 px-2">
          <div className="bg-white shadow rounded-lg border-0 overflow-hidden">
            <Link href="/movies-detail">
              <div className="relative">
                <div className="absolute bg-white shadow-sm rounded text-center p-2 m-2 top-0 left-0">
                  <h6 className="text-gray-900 mb-0 font-bold"><FaHeart className="inline text-red-500" /> 88%</h6>
                  <small className="text-gray-500">23,421</small>
                </div>
                <img src="/img/m1.jpg" className="w-full h-auto" alt="Jumanji" />
              </div>
              <div className="p-3">
                <h5 className="text-lg font-bold text-gray-900 mb-1">Jumanji: The Next Level</h5>
                <p className="text-sm">
                  <small className="text-gray-500">English</small> 
                  <small className="text-red-500 ml-2">
                    <FaCalendarAlt className="inline text-gray-400" /> 22 AUG
                  </small>
                </p>
              </div>
            </Link>
          </div>
        </div>

        {/* 卡片 2 (重複結構) */}
        <div className="w-full xl:w-1/4 md:w-1/2 mb-4 px-2">
          <div className="bg-white shadow rounded-lg border-0 overflow-hidden">
            <Link href="/movies-detail">
              <div className="relative">
                <div className="absolute bg-white shadow-sm rounded text-center p-2 m-2 top-0 left-0">
                  <h6 className="text-gray-900 mb-0 font-bold"><FaHeart className="inline text-red-500" /> 50%</h6>
                  <small className="text-gray-500">8,784</small>
                </div>
                <img src="/img/m2.jpg" className="w-full h-auto" alt="Gemini Man" />
              </div>
              <div className="p-3">
                <h5 className="text-lg font-bold text-gray-900 mb-1">Gemini Man</h5>
                <p className="text-sm">
                  <small className="text-gray-500">English</small> 
                  <small className="text-red-500 ml-2">
                    <FaCalendarAlt className="inline text-gray-400" /> 22 AUG
                  </small>
                </p>
              </div>
            </Link>
          </div>
        </div>
        
        {/* 卡片 3 (重複結構) */}
        <div className="w-full xl:w-1/4 md:w-1/2 mb-4 px-2">
           <div className="bg-white shadow rounded-lg border-0 overflow-hidden">
            <Link href="/movies-detail">
              <div className="relative">
                <div className="absolute bg-white shadow-sm rounded text-center p-2 m-2 top-0 left-0">
                  <h6 className="text-gray-900 mb-0 font-bold"><FaHeart className="inline text-red-500" /> 20%</h6>
                  <small className="text-gray-500">69,123</small>
                </div>
                <img src="/img/m3.jpg" className="w-full h-auto" alt="The Current War" />
              </div>
              <div className="p-3">
                <h5 className="text-lg font-bold text-gray-900 mb-1">The Current War</h5>
                <p className="text-sm">
                  <small className="text-gray-500">English</small> 
                  <small className="text-red-500 ml-2">
                    <FaCalendarAlt className="inline text-gray-400" /> 22 AUG
                  </small>
                </p>
              </div>
            </Link>
          </div>
        </div>
        
        {/* 卡片 4 (重複結構) */}
        <div className="w-full xl:w-1/4 md:w-1/2 mb-4 px-2">
           <div className="bg-white shadow rounded-lg border-0 overflow-hidden">
            <Link href="/movies-detail">
              <div className="relative">
                <div className="absolute bg-white shadow-sm rounded text-center p-2 m-2 top-0 left-0">
                  <h6 className="text-gray-900 mb-0 font-bold"><FaHeart className="inline text-red-500" /> 74%</h6>
                  <small className="text-gray-500">88,865</small>
                </div>
                <img src="/img/m4.jpg" className="w-full h-auto" alt="Charlie's Angels" />
              </div>
              <div className="p-3">
                <h5 className="text-lg font-bold text-gray-900 mb-1">Charlie's Angels</h5>
                <p className="text-sm">
                  <small className="text-gray-500">English</small> 
                  <small className="text-red-500 ml-2">
                    <FaCalendarAlt className="inline text-gray-400" /> 22 AUG
                  </small>
                </p>
              </div>
            </Link>
          </div>
        </div>

      </div>
      
      {/* --- [修改！] "Collections" 區塊已被刪除 --- */}

    </div>
  );
}