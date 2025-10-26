import { Api } from "@/lib/api";
import { USE_MOCKS } from "@/lib/config";
import type { Profile } from "@/lib/types";

export async function getMyProfile(): Promise<Profile> {
  if (USE_MOCKS) {
    return {
      username: "demo_user",
      watchlist: [
        { id: "10", title: "The Godfather", year: 1972, rating: 9.2 },
        { id: "11", title: "Heat", year: 1995, rating: 8.3 },
      ],
    };
  }
  return Api.profile.me();
}
