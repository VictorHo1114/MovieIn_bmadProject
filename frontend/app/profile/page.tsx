// app/profile/page.tsx
import { getMyProfile } from "@/features/profile/services";
export default async function Page() {
  const me = await getMyProfile();
  return <pre>{JSON.stringify(me, null, 2)}</pre>;
}