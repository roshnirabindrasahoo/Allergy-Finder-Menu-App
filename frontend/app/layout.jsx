export const metadata = { title: 'Allergy-Friendly Menu Finder' }

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <div className="container">
          <header style={{marginBottom: 8}}>
            <h1>Allergy-Friendly Menu Finder</h1>
          </header>
          {children}
        </div>
      </body>
    </html>
  )
}
