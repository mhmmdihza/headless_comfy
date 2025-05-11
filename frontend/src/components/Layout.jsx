import Topbar from './Topbar';

export default function Layout({ children, setActiveMenu, activeMenu }) {
  return (
    <section className="bg-gray-50 dark:bg-gray-900 min-h-screen py-10 px-4">
      <div className="max-w-4xl mx-auto space-y-8">
        <Topbar setActiveMenu={setActiveMenu} activeMenu={activeMenu} />
        {children}
      </div>
    </section>
  );
}
