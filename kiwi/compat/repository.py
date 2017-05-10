# TODO: Webkit


_installed_constants = False
constants = [
    ('Gtk', 'ACCEL_', 'AccelFlags'),
    ('Gtk', 'ARROW_', 'ArrowType'),
    ('Gtk', 'ASSISTANT_PAGE_', 'AssistantPageType'),
    ('Gtk', 'BUTTONBOX_', 'ButtonBoxStyle'),
    ('Gtk', 'BUTTONS_', 'ButtonsType'),
    ('Gtk', 'CELL_RENDERER_MODE_', 'CellRendererMode'),
    ('Gtk', 'CORNER_', 'CornerType'),
    ('Gtk', 'DIALOG_', 'DialogFlags'),
    ('Gtk', 'ENTRY_ICON_', 'EntryIconPosition'),
    ('Gtk', 'FILE_CHOOSER_ACTION_', 'FileChooserAction'),
    ('Gtk', 'ICON_LOOKUP_', 'IconLookupFlags'),
    ('Gtk', 'ICON_SIZE_', 'IconSize'),
    ('Gtk', 'IMAGE_', 'ImageType'),
    ('Gtk', 'JUSTIFY_', 'Justification'),
    ('Gtk', 'MESSAGE_', 'MessageType'),
    ('Gtk', 'MOVEMENT_', 'MovementStep'),
    ('Gtk', 'ORIENTATION_', 'Orientation'),
    ('Gtk', 'POLICY_', 'PolicyType'),
    ('Gtk', 'POS_', 'PositionType'),
    ('Gtk', 'RECENT_FILTER_', 'RecentFilterFlags'),
    ('Gtk', 'RECENT_SORT_', 'RecentSortType'),
    ('Gtk', 'RELIEF_', 'ReliefStyle'),
    ('Gtk', 'RESPONSE_', 'ResponseType'),
    ('Gtk', 'SELECTION_', 'SelectionMode'),
    ('Gtk', 'SHADOW_', 'ShadowType'),
    ('Gtk', 'SIZE_GROUP_', 'SizeGroupMode'),
    ('Gtk', 'SORT_', 'SortType'),
    ('Gtk', 'STATE_', 'StateType'),
    ('Gtk', 'TARGET_', 'TargetFlags'),
    ('Gtk', 'TEXT_DIR_', 'TextDirection'),
    ('Gtk', 'TEXT_SEARCH_', 'TextSearchFlags'),
    ('Gtk', 'TEXT_WINDOW_', 'TextWindowType'),
    ('Gtk', 'TOOLBAR_', 'ToolbarStyle'),
    ('Gtk', 'TREE_MODEL_', 'TreeModelFlags'),
    ('Gtk', 'TREE_VIEW_COLUMN_', 'TreeViewColumnSizing'),
    ('Gtk', 'TREE_VIEW_DROP_', 'TreeViewDropPosition'),
    ('Gtk', 'WINDOW_', 'WindowType'),
    ('Gtk', 'DEST_DEFAULT_', 'DestDefaults'),
    ('Gtk', 'WIN_POS_', 'WindowPosition'),
    ('Gtk', 'WRAP_', 'WrapMode'),
    ('Gtk', 'UI_MANAGER_', 'UIManagerItemType'),
    ('Gtk', 'FILL', 'AttachOptions'),
    ('Gtk', 'EXPAND', 'AttachOptions'),
    ('Gtk', 'SHRINK', 'AttachOptions'),

    ("Gdk", "WINDOW_TYPE_HINT_", "WindowTypeHint"),
    ("Gdk", "SHIFT_MASK", "ModifierType"),
    ("Gdk", "LOCK_MASK", "ModifierType"),
    ("Gdk", "CONTROL_MASK", "ModifierType"),
    ("Gdk", "MOD1_MASK", "ModifierType"),
    ("Gdk", "MOD2_MASK", "ModifierType"),
    ("Gdk", "MOD3_MASK", "ModifierType"),
    ("Gdk", "MOD4_MASK", "ModifierType"),
    ("Gdk", "MOD5_MASK", "ModifierType"),
    ("Gdk", "BUTTON1_MASK", "ModifierType"),
    ("Gdk", "BUTTON2_MASK", "ModifierType"),
    ("Gdk", "BUTTON3_MASK", "ModifierType"),
    ("Gdk", "BUTTON4_MASK", "ModifierType"),
    ("Gdk", "BUTTON5_MASK", "ModifierType"),
    ("Gdk", "RELEASE_MASK", "ModifierType"),
    ("Gdk", "MODIFIER_MASK", "ModifierType"),
    ("Gdk", "VISIBILITY_FULLY_OBSCURED", "VisibilityState"),
    ("Gdk", "NOTIFY_", "NotifyType"),
    ("Gdk", "PROP_MODE_", "PropMode"),
    ("Gdk", "BUTTON_PRESS", "EventType"),
    ("Gdk", "ACTION_", "DragAction"),
    ("Gdk", "GRAB_", "GrabStatus"),
    ("Gdk", "SCROLL_", "ScrollDirection"),
    ('Gdk', 'BUTTON_PRESS_MASK', 'EventMask'),
    ('Gdk', 'BUTTON_RELEASE_MASK', 'EventMask'),
    ('Gdk', 'ENTER_NOTIFY_MASK', 'EventMask'),
    ('Gdk', 'KEY_PRESS_MASK', 'EventMask'),
    ('Gdk', 'LEAVE_NOTIFY_MASK', 'EventMask'),
    ('Gdk', 'POINTER_MOTION_MASK', 'EventMask'),

    ('Pango', 'ALIGN_', 'Alignment'),
    ('Pango', 'ELLIPSIZE_', 'EllipsizeMode'),
    ('Pango', 'STYLE_', 'Style'),
    ('Pango', 'UNDERLINE_', 'Underline'),
    ('Pango', 'WEIGHT_', 'Weight'),
    ('Pango', 'WRAP_', 'WrapMode'),
    ('Pango', 'TAB_', 'TabAlign'),
]


if True:
    import gtk as Gtk
    import gtk.gdk as Gdk
    import glib as GLib
    import gobject as GObject
    import pango as Pango
    import gio as Gio

    GObject.Property = GObject.property

    if not _installed_constants:
        for module, original, new in constants:
            module = locals()[module]
            enum = getattr(module, new)
            for key in filter(lambda x: x.startswith(original), dir(module)):
                value = getattr(module, key)
                if original.endswith('_'):
                    name = key[len(original):]
                else:
                    name = key
                setattr(enum, name, value)
        _installed_constants = True

        # keysyms is a lazy module. Access some attributes just to make sure it
        # loads
        Gtk.keysyms.a
        for key in Gtk.keysyms.__dict__:
            setattr(Gdk, 'KEY_' + key, getattr(Gtk.keysyms, key))

else:
    from gi.repository import Gtk, Gdk, GLib, GObject, Gio, Pango


__all__ = [Gtk, Gdk, GLib, GObject, Gio, Pango]
