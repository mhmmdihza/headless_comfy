import { Link } from 'react-router-dom';
import { supabase } from '../supabaseClient';


export default function Topbar({ setActiveMenu, activeMenu }) {
  const handleLogout = async () => {
    await supabase.auth.signOut();
    window.location.href = '/';
  };

  const menuItems = [
    { label: 'Img2Img Flux', link: '#img2img_flux' },
    { label: 'Img2Img Flux Inpainting', link: '#img2img_flux_inpainting' },
    { label: 'Img2Img Flux Outpainting', link: '#img2img_flux_outpanting' },
  ];

  const handleMenuClick = (menu) => {
    setActiveMenu(menu);
  };

  return (
    <div className="flex justify-between items-center bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
      <h1 className="text-xl font-bold text-gray-800 dark:text-white">Menu</h1>
      <div className="flex space-x-4">
        {menuItems.map((item, index) => (
          <Link
            key={index}
            to={item.link}
            onClick={() => handleMenuClick(item.label)}
            className={`px-3 py-2 rounded transition-all duration-200
              ${
                activeMenu === item.label
                  ? 'bg-blue-100 dark:bg-blue-600 text-blue-800 dark:text-white font-semibold'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
              }`}
          >
            {item.label}
          </Link>
        ))}
      </div>
      <button
        onClick={handleLogout}
        className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded"
      >
        Logout
      </button>
    </div>
  );
}
