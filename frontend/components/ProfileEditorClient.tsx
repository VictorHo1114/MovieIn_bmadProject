"use client";
import dynamic from 'next/dynamic';
import React from 'react';

const ProfileEditor = dynamic(() => import('./ProfileEditor'), { ssr: false });

export default function ProfileEditorClient(props: any) {
  return <ProfileEditor {...props} />;
}
