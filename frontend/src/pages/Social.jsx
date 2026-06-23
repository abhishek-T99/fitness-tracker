import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Heart, MessageCircle, Send, UserPlus, Users } from "lucide-react";
import { formatDistanceToNow, parseISO } from "date-fns";
import toast from "react-hot-toast";

import PageHeader from "../components/PageHeader.jsx";
import { socialApi } from "../api/endpoints.js";
import { qk } from "../api/queryKeys.js";

export default function Social() {
  const [tab, setTab] = useState("feed");
  return (
    <div>
      <PageHeader title="Social" subtitle="Share progress and stay accountable" />
      <div className="flex gap-2 mb-6 border-b border-slate-200">
        {[
          { value: "feed", label: "Feed" },
          { value: "friends", label: "Friends" },
          { value: "find", label: "Find people" },
        ].map((t) => (
          <button
            key={t.value}
            onClick={() => setTab(t.value)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${
              tab === t.value
                ? "border-brand-600 text-brand-600"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>
      {tab === "feed" && <Feed />}
      {tab === "friends" && <Friends />}
      {tab === "find" && <FindPeople />}
    </div>
  );
}

function Feed() {
  const queryClient = useQueryClient();
  const [body, setBody] = useState("");
  const { data } = useQuery({ queryKey: qk.social.feed(), queryFn: socialApi.feed });
  const posts = data?.results || data || [];

  const createPost = useMutation({
    mutationFn: (b) => socialApi.createPost({ body: b }),
    onSuccess: () => {
      setBody("");
      toast.success("Posted");
      queryClient.invalidateQueries({ queryKey: qk.social.feed() });
    },
  });

  const like = useMutation({
    mutationFn: (id) => socialApi.likePost(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: qk.social.feed() }),
  });

  return (
    <div className="space-y-4">
      <div className="card p-4">
        <textarea
          rows={3}
          className="input"
          placeholder="What's on your mind?"
          value={body}
          onChange={(e) => setBody(e.target.value)}
        />
        <div className="flex justify-end mt-3">
          <button
            disabled={!body.trim() || createPost.isPending}
            onClick={() => createPost.mutate(body.trim())}
            className="btn-primary"
          >
            <Send className="w-4 h-4" /> Post
          </button>
        </div>
      </div>

      {posts.length === 0 && (
        <p className="text-center text-slate-500 py-8">
          No posts yet. Add friends or share your first update.
        </p>
      )}

      {posts.map((post) => (
        <article key={post.id} className="card p-5">
          <header className="flex items-center gap-3 mb-3">
            <div className="h-10 w-10 rounded-full bg-brand-600 text-white flex items-center justify-center font-semibold">
              {(post.user_detail.first_name?.[0] || post.user_detail.username?.[0] || "?").toUpperCase()}
            </div>
            <div>
              <p className="font-semibold text-sm">
                {post.user_detail.first_name || post.user_detail.username}
              </p>
              <p className="text-xs text-slate-500">
                {formatDistanceToNow(parseISO(post.created_at), { addSuffix: true })}
              </p>
            </div>
          </header>
          <p className="text-slate-700 whitespace-pre-wrap mb-3">{post.body}</p>
          <div className="flex items-center gap-4 text-sm text-slate-500">
            <button
              onClick={() => like.mutate(post.id)}
              className={`flex items-center gap-1 hover:text-rose-500 ${
                post.liked_by_me ? "text-rose-500" : ""
              }`}
            >
              <Heart className={`w-4 h-4 ${post.liked_by_me ? "fill-current" : ""}`} />
              {post.likes_count}
            </button>
            <CommentBox post={post} />
          </div>
          {post.comments?.length > 0 && (
            <div className="mt-4 pt-4 border-t border-slate-100 space-y-2">
              {post.comments.map((c) => (
                <div key={c.id} className="text-sm">
                  <span className="font-semibold">
                    {c.user_detail.first_name || c.user_detail.username}:{" "}
                  </span>
                  <span className="text-slate-700">{c.body}</span>
                </div>
              ))}
            </div>
          )}
        </article>
      ))}
    </div>
  );
}

function CommentBox({ post }) {
  const queryClient = useQueryClient();
  const [val, setVal] = useState("");
  const [open, setOpen] = useState(false);
  const submit = useMutation({
    mutationFn: () => socialApi.commentOnPost(post.id, val),
    onSuccess: () => {
      setVal("");
      setOpen(false);
      queryClient.invalidateQueries({ queryKey: qk.social.feed() });
    },
  });
  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-1 hover:text-brand-600"
      >
        <MessageCircle className="w-4 h-4" /> Comment
      </button>
    );
  }
  return (
    <div className="flex-1 flex gap-2">
      <input
        className="input py-1 flex-1"
        autoFocus
        value={val}
        onChange={(e) => setVal(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && val.trim() && submit.mutate()}
        placeholder="Write a comment…"
      />
      <button
        onClick={() => val.trim() && submit.mutate()}
        className="btn-primary py-1"
      >
        Send
      </button>
    </div>
  );
}

function Friends() {
  const queryClient = useQueryClient();
  const { data: friends } = useQuery({
    queryKey: qk.social.friends(),
    queryFn: socialApi.friends,
  });
  const { data: requests } = useQuery({
    queryKey: qk.social.friendships(),
    queryFn: socialApi.friendships,
  });
  const pending =
    (requests?.results || requests || []).filter((f) => f.status === "pending") || [];

  const accept = useMutation({
    mutationFn: (id) => socialApi.acceptRequest(id),
    onSuccess: () => {
      toast.success("Friend added");
      queryClient.invalidateQueries({ queryKey: qk.social.friends() });
      queryClient.invalidateQueries({ queryKey: qk.social.friendships() });
    },
  });
  const decline = useMutation({
    mutationFn: (id) => socialApi.declineRequest(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: qk.social.friendships() }),
  });

  return (
    <div className="space-y-6">
      {pending.length > 0 && (
        <div className="card">
          <div className="card-header"><h3 className="font-semibold">Pending requests</h3></div>
          <div className="card-body space-y-2">
            {pending.map((f) => (
              <div key={f.id} className="flex items-center justify-between">
                <p className="text-sm font-medium">
                  {f.requester_detail.first_name || f.requester_detail.username}
                </p>
                <div className="flex gap-2">
                  <button onClick={() => accept.mutate(f.id)} className="btn-primary py-1 text-xs">
                    Accept
                  </button>
                  <button onClick={() => decline.mutate(f.id)} className="btn-secondary py-1 text-xs">
                    Decline
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="card">
        <div className="card-header"><h3 className="font-semibold">Your friends</h3></div>
        <div className="card-body">
          {(friends || []).length === 0 ? (
            <p className="text-sm text-slate-500">No friends yet. Use Find people to add some.</p>
          ) : (
            <ul className="divide-y divide-slate-100">
              {(friends || []).map((f) => (
                <li key={f.id} className="py-2 flex items-center gap-3">
                  <div className="h-9 w-9 rounded-full bg-brand-600 text-white flex items-center justify-center font-semibold">
                    {(f.first_name?.[0] || f.username?.[0] || "?").toUpperCase()}
                  </div>
                  <div>
                    <p className="text-sm font-medium">
                      {f.first_name || f.username} {f.last_name}
                    </p>
                    <p className="text-xs text-slate-500">@{f.username}</p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

function FindPeople() {
  const queryClient = useQueryClient();
  const [q, setQ] = useState("");
  const { data } = useQuery({
    queryKey: qk.social.searchUsers(q),
    queryFn: () => socialApi.searchUsers(q),
    enabled: q.length > 1,
  });
  const users = data?.results || [];

  const sendReq = useMutation({
    mutationFn: (id) => socialApi.sendRequest(id),
    onSuccess: () => {
      toast.success("Request sent");
      queryClient.invalidateQueries({ queryKey: qk.social.friendships() });
    },
  });

  return (
    <div>
      <input
        className="input mb-4"
        placeholder="Search by username or name…"
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />
      <div className="space-y-2">
        {users.map((u) => (
          <div key={u.id} className="card p-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-9 w-9 rounded-full bg-brand-600 text-white flex items-center justify-center font-semibold">
                {(u.first_name?.[0] || u.username?.[0] || "?").toUpperCase()}
              </div>
              <div>
                <p className="text-sm font-medium">
                  {u.first_name || u.username} {u.last_name}
                </p>
                <p className="text-xs text-slate-500">@{u.username}</p>
              </div>
            </div>
            <button
              onClick={() => sendReq.mutate(u.id)}
              className="btn-secondary"
            >
              <UserPlus className="w-4 h-4" /> Add
            </button>
          </div>
        ))}
        {q.length > 1 && users.length === 0 && (
          <p className="text-center text-sm text-slate-500 py-6">No matches.</p>
        )}
        {q.length <= 1 && (
          <p className="text-center text-sm text-slate-400 py-6 flex items-center justify-center gap-2">
            <Users className="w-4 h-4" /> Type at least 2 characters to search.
          </p>
        )}
      </div>
    </div>
  );
}
