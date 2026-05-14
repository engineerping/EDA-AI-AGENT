import 'react'

declare module 'react' {
  namespace JSX {
    interface IntrinsicElements {
      'kicanvas-embed': React.DetailedHTMLProps<React.HTMLAttributes<HTMLElement> & { controls?: string }, HTMLElement>
    }
  }
}
