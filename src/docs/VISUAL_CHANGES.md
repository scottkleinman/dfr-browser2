# Visual Changes Quick Reference

## Color Palette

### Primary Blue

- Primary-600: `#1e88e5` (main brand color for links, buttons)
- Primary-700: `#1976d2` (hover states, headers)
- Primary-50: `#e3f2fd` (backgrounds, hover backgrounds)

### Neutrals

- Neutral-900: `#212121` (headings)
- Neutral-800: `#424242` (body text)
- Neutral-700: `#616161` (secondary text)
- Neutral-600: `#757575` (muted text)

## Typography

### Fonts

```css
Sans-serif: Inter (UI elements, navigation, buttons)
Serif: Source Serif 4 (content areas if needed)
Monospace: Fira Code (code snippets)
```

### Size Scale

```txt
h1: 3.052rem (48.83px)
h2: 2.441rem (39px)
h3: 1.953rem (31.25px)
h4: 1.563rem (25px)
h5: 1.25rem (20px)
Body: 1rem (16px)
Small: 0.8rem (12.8px)
```

## Spacing

```txt
space-1: 4px
space-2: 8px
space-3: 12px
space-4: 16px
space-5: 24px
space-6: 32px
space-7: 48px
```

## Border Radius

```txt
sm: 6px (inputs, small elements)
md: 8px (buttons, form controls)
lg: 12px (cards, modals)
xl: 16px (large cards)
```

## Shadows

```txt
sm: Subtle (default cards)
md: Medium (hover states)
lg: Large (elevated cards)
xl: Extra large (focus states)
2xl: Dramatic (modals, notifications)
```

## Key Visual Changes

### Before → After

1. **Background**:
   - Before: Flat `#f8f9fa`
   - After: Gradient from light gray to light blue

2. **Cards**:
   - Before: Basic white with subtle shadow
   - After: Glass effect with backdrop blur, gradient hover

3. **Buttons**:
   - Before: Solid Bootstrap blue
   - After: Gradient blue with lift on hover

4. **Navigation**:
   - Before: Standard Bootstrap nav
   - After: Active underline indicator, hover backgrounds

5. **Typography**:
   - Before: Default Bootstrap (system fonts)
   - After: Inter font with improved hierarchy

6. **Modals**:
   - Before: Standard white with borders
   - After: Gradient header, dramatic shadows, rounded corners

7. **Forms**:
   - Before: Standard Bootstrap inputs
   - After: Focus rings with brand color, better spacing

## Quick Customization Guide

Want to change the primary color? Edit these in `style.css`:

```css
:root {
  --color-primary-600: #1e88e5; /* Your main color */
  --color-primary-700: #1976d2; /* Darker version */
  --color-primary-50: #e3f2fd;  /* Lightest version */
}
```

The entire app will update automatically!
