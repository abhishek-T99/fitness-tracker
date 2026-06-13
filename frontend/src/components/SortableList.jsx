/**
 * SortableList — thin wrapper around @dnd-kit that handles:
 *   - Drag-and-drop reordering for any list of items
 *   - Keyboard accessibility (built into dnd-kit)
 *   - Optimistic local reorder → calls onReorder(newIds) when the drag ends
 *
 * Usage
 * ─────
 *   <SortableList ids={items.map(i => i.id)} onReorder={handleReorder}>
 *     {items.map(item => (
 *       <SortableItem key={item.id} id={item.id}>
 *         {(dragHandleProps) => <YourCard dragHandleProps={dragHandleProps} />}
 *       </SortableItem>
 *     ))}
 *   </SortableList>
 *
 * dragHandleProps must be spread onto the element the user drags from.
 * If you want the whole card to be draggable, spread them on the card root.
 */
import {
  DndContext,
  DragOverlay,
  KeyboardSensor,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import {
  SortableContext,
  arrayMove,
  rectSortingStrategy,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical } from "lucide-react";
import { useState } from "react";

// ── SortableItem ─────────────────────────────────────────────────────────────
export function SortableItem({ id, children }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
    zIndex: isDragging ? 10 : undefined,
  };

  const dragHandleProps = { ...attributes, ...listeners };

  return (
    <div ref={setNodeRef} style={style}>
      {children(dragHandleProps)}
    </div>
  );
}

// ── DragHandle ───────────────────────────────────────────────────────────────
export function DragHandle({ dragHandleProps, className = "" }) {
  return (
    <button
      type="button"
      {...dragHandleProps}
      className={`flex items-center justify-center cursor-grab active:cursor-grabbing text-slate-300 hover:text-slate-500 transition-colors touch-none ${className}`}
      aria-label="Drag to reorder"
    >
      <GripVertical className="w-4 h-4" />
    </button>
  );
}

// ── SortableList ─────────────────────────────────────────────────────────────
/**
 * @param {string[]}  ids       Ordered list of string IDs (must match SortableItem ids)
 * @param {function}  onReorder Called with the new ordered ID array after a drag
 * @param {string}    strategy  "vertical" | "grid" (default "vertical")
 * @param {ReactNode} children  SortableItem elements
 * @param {string}    className Wrapper class
 */
export default function SortableList({
  ids,
  onReorder,
  strategy = "vertical",
  children,
  className = "",
}) {
  const [activeId, setActiveId] = useState(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  const sortingStrategy =
    strategy === "grid" ? rectSortingStrategy : verticalListSortingStrategy;

  function handleDragStart({ active }) {
    setActiveId(active.id);
  }

  function handleDragEnd({ active, over }) {
    setActiveId(null);
    if (!over || active.id === over.id) return;

    const oldIndex = ids.indexOf(active.id);
    const newIndex = ids.indexOf(over.id);
    const newIds = arrayMove(ids, oldIndex, newIndex);
    onReorder(newIds);
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <SortableContext items={ids} strategy={sortingStrategy}>
        <div className={className}>{children}</div>
      </SortableContext>
    </DndContext>
  );
}
