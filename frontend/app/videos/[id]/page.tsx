"use client";
import { redirect } from "next/navigation";

// Individual video detail routes to the same results view (protected video
// player + download/delete). Kept separate per SRS route list (/videos/:id)
// in case you want a distinct read-only detail view later.
export default function VideoDetailRedirect({ params }: { params: { id: string } }) {
  redirect(`/results/${params.id}`);
}
