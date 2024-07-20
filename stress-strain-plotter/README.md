# Stress-Strain Plotter

This is a Next.js application that allows users to plot stress-strain data and calculate material properties. The application provides an interactive interface for inputting stress and strain values, visualizing the data on a chart, and computing key material characteristics.

## Features

- Input stress and strain data points
- Plot stress vs strain curve using Recharts
- Calculate and display material properties:
  - Tensile Strength
  - Young's Modulus
  - Yield Strength (0.2% offset method)
- Responsive design using Tailwind CSS
- Clear data functionality

## Getting Started

1. Clone the repository
2. Install dependencies: `npm install`
3. Run the development server: `npm run dev`
4. Open [http://localhost:3000](http://localhost:3000) in your browser

## Technologies Used

- Next.js
- React
- TypeScript
- Recharts
- Tailwind CSS
- Shadcn UI components

## Project Structure

- `src/components/StressStrainPlotter.tsx`: Main component for the stress-strain plotter
- `src/app/page.tsx`: Main page component
- `src/app/layout.tsx`: Root layout component
- `src/components/ui/`: UI components from Shadcn
- `src/lib/utils.ts`: Utility functions

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the [MIT License](LICENSE).