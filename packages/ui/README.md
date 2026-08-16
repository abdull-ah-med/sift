# @sift/ui

shadcn-derived primitives and complete-block building blocks for sift, rethemed to
`rules/design-philosophy.mdc` (§1 palette, §2 SF Pro Display).

Prefer composing from these exports over hand-rolling chrome. Source: shadcn/ui
new-york (copy-in, MIT). `components.json` is the registry config for later
`shadcn add` into this package.

**Kit (p4ui-1):** Button, Input, Textarea, Label, Checkbox, Switch, Card, Badge,
Skeleton, Avatar, Table, Dialog, Sheet, DropdownMenu, Select, Tabs, Tooltip,
Popover, Collapsible, ScrollArea, Breadcrumb, Sidebar (sidebar-07 primitives),
Toaster (sonner).

Brand teal (`--sift-accent`) maps to shadcn `--primary` / `--ring` only.
shadcn `--accent` (hover surface) maps to `--sift-surface`, not teal.
