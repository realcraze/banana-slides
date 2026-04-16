import { useEffect, useRef, useState } from 'react';
import { ChevronDown, LogOut } from 'lucide-react';
import { useAuth } from '@/auth/AuthContext';

const ACCESS_CODE_STORAGE_KEY = 'banana-access-code';

function getDisplayName(name?: string | null, email?: string | null): string {
  const trimmedName = name?.trim();
  if (trimmedName && !trimmedName.includes('@') && trimmedName.length <= 40) {
    return trimmedName;
  }
  const localPart = email?.split('@')[0]?.trim();
  return localPart || 'User';
}

function getInitials(label: string): string {
  const parts = label
    .replace(/[._-]+/g, ' ')
    .split(/\s+/)
    .filter(Boolean);

  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  }
  return label.slice(0, 2).toUpperCase();
}

export function UserMenu() {
  const { me } = useAuth();
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const displayName = getDisplayName(me.name, me.email);
  const initials = getInitials(displayName);
  const avatarUrl = me.avatar_url || '';

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (!menuRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSignOut = () => {
    localStorage.removeItem(ACCESS_CODE_STORAGE_KEY);
    window.location.href = '/oauth2/sign_out?rd=/';
  };

  if (!me.authenticated) {
    return null;
  }

  return (
    <div className="relative" ref={menuRef}>
      <button
        type="button"
        onClick={() => setOpen(prev => !prev)}
        className="flex h-9 items-center gap-2 rounded-full border border-white/70 bg-white/70 px-2 text-left shadow-sm backdrop-blur transition-all hover:bg-banana-50/80 hover:shadow-md dark:border-border-primary dark:bg-background-secondary/80 dark:hover:bg-background-hover"
        aria-label="Account menu"
      >
        {avatarUrl ? (
          <img src={avatarUrl} alt="" className="h-7 w-7 shrink-0 rounded-full object-cover shadow-sm" />
        ) : (
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-banana-400 to-orange-500 text-xs font-bold text-gray-950 shadow-sm">
            {initials}
          </span>
        )}
        <span className="hidden min-w-0 max-w-[150px] md:block">
          <span className="block truncate text-sm font-medium leading-none text-gray-900 dark:text-foreground-primary">
            {displayName}
          </span>
        </span>
        <ChevronDown size={14} className={`text-gray-500 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="absolute right-0 top-full z-50 mt-2 w-64 overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-xl dark:border-border-primary dark:bg-background-secondary">
          <div className="border-b border-gray-100 px-4 py-3 dark:border-border-primary">
            <div className="flex items-center gap-3">
              {avatarUrl ? (
                <img src={avatarUrl} alt="" className="h-10 w-10 shrink-0 rounded-full object-cover" />
              ) : (
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-banana-400 to-orange-500 text-sm font-bold text-gray-950">
                  {initials}
                </span>
              )}
              <div className="min-w-0">
                <div className="truncate text-sm font-semibold text-gray-900 dark:text-foreground-primary">
                  {displayName}
                </div>
                {me.email && (
                  <div className="truncate text-xs text-gray-500 dark:text-foreground-tertiary">
                    {me.email}
                  </div>
                )}
              </div>
            </div>
          </div>

          <button
            type="button"
            onClick={handleSignOut}
            className="flex w-full items-center gap-2 px-4 py-3 text-sm font-medium text-red-600 transition-colors hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950/30"
          >
            <LogOut size={16} />
            Sign out
          </button>
        </div>
      )}
    </div>
  );
}
