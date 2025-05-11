import { useEffect, useState } from 'react';
import Img2ImgFlux from '../components/Img2imgFlux';
import Layout from '../components/Layout';
import { useApi } from '../services/Api';


export default function Dashboard() {
  const [loading, setLoading] = useState(false);
  const [queues, setQueues] = useState([]);
  const {getQueues, getStatus, subscribeToQueueStatus} = useApi();
  const [selectedStatus, setSelectedStatus] = useState(null);
  const [selectedImage, setSelectedImage] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [activeMenu, setActiveMenu] = useState('Home');

  useEffect(() => {
    const fetchQueues = async () => {
      try {
        const data = await getQueues();
        setQueues(data);
      } catch {
        alert('Error fetching queues');
      }
    };

    fetchQueues();
  }, [getQueues]);

  useEffect(() => {
    const unsubscribers = [];
  
    queues.forEach((queue) => {
      if (queue.status !== 'COMPLETED' && queue.status !== 'FAILED') {
        const unsubscribe = subscribeToQueueStatus(queue.s3_object_id, (newStatus) => {
          setQueues((prev) =>
            prev.map((q) =>
              q.s3_object_id === queue.s3_object_id ? { ...q, status: newStatus } : q
            )
          );
        });
  
        unsubscribers.push(unsubscribe);
      }
    });
  
    return () => {
      unsubscribers.forEach((unsubscribe) => unsubscribe());
    };
  }, [queues, subscribeToQueueStatus]);
  
  

  const handleQueueClick = async (jobId) => {
    setLoading(true);
    try {
      const { status, imageUrl } = await getStatus(jobId);
      setSelectedStatus(status);
      setSelectedImage(imageUrl);
      setModalVisible(true);
    } catch (err) {
      alert(`Error checking status: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const renderContent = () => {
    switch (activeMenu) {
      case 'Img2Img Flux':
        return <Img2ImgFlux/>
      case 'Img2Img Flux Inpainting':
        return <h2>Not available</h2>
      case 'Img2Img Flux Outpainting':
        return <h2>Not available</h2>
      default:
        return null;
    }
  };

  return (
    <Layout setActiveMenu={setActiveMenu} activeMenu={activeMenu}>
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow space-y-4">
        {renderContent()}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-100 mb-4">
              Queues
            </h3>
            {queues.length === 0 ? (
              <p className="text-gray-500 dark:text-gray-400">No queues available</p>
            ) : (
              <ul className="space-y-4">
                {queues.map((queue, index) => (
                  <li key={index} className="bg-gray-100 dark:bg-gray-700 p-4 rounded">
                    <p>
                      <span className="font-semibold text-gray-700 dark:text-gray-200">
                        ID:
                      </span>{' '}
                      <button
                        onClick={() => handleQueueClick(queue.s3_object_id)}
                        className="text-blue-600 dark:text-blue-400 underline hover:text-blue-800 dark:hover:text-blue-300"
                      >
                        {queue.s3_object_id}
                      </button>
                    </p>
                    <p className="text-gray-700 dark:text-gray-300">Status: {queue.status}</p>
                    <p className="text-gray-700 dark:text-gray-300">
                      Created On: {queue.created_on}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </div>     
          {modalVisible && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg max-w-md w-full">
                <h3 className="text-lg font-bold mb-4 text-gray-800 dark:text-gray-100">
                  Status: {selectedStatus}
                </h3>
                {selectedImage ? (
                  <img src={selectedImage} alt="Job result" className="w-full rounded mb-4" />
                ) : (
                  <p className="text-gray-700 dark:text-gray-300">No image available</p>
                )}
                <button
                  onClick={() => setModalVisible(false)}
                  disabled={loading}
                  className="bg-gray-700 text-white px-4 py-2 rounded hover:bg-gray-800"
                >
                  Close
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
