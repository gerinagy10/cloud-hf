import React, { useEffect, useState } from 'react';
import { socket } from './socketClient';

interface ImageTextPair {
  id: string;
  base64Image: string;
  text: string;
  humanCount: number;
}

const App: React.FC = () => {
  const [data, setData] = useState<ImageTextPair[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [description, setDescription] = useState('');

  // Fetch image-text pairs from the API on component mount
  useEffect(() => {
    fetchData();

    socket.on("data_processed", (data) => {
      console.log("Received from server");
      
      const newItem: ImageTextPair = {
        id: data.sid,
        base64Image: "data:image/jpeg;base64," + data.image,
        text: data.text,
        humanCount: data.human_count,
      };
    
      setData((prevData) => [...prevData, newItem]);
    });

    // Clean up on unmount
    return () => {
      socket.off("data_processed");
    };
  }, []);

  // Function to get data from our API endpoint
  const fetchData = async () => {
    try {
      // const response = await fetch('/api/image-text');
      // if (!response.ok) {
      //   throw new Error('Network response was not ok');
      // }
      // const result: ImageTextPair[] = await response.json();

      //setData(sampleData);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };


  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };


  const handleUpload = async () => {
    if (!selectedFile || !description) {
      return;
    }

    const base64 = await fileToBase64(selectedFile);

    socket.emit("process_data", {
      text: description,
      image: base64,
    });

    setDescription("")
    setSelectedFile(null)
  };

  async function fileToBase64(file: File): Promise<string> {
    return await new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }
  

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto', fontFamily: 'Arial, sans-serif' }}>
      
      {/* Upload Form */}
      <div style={{ marginTop: '20px', padding: '10px', border: '1px solid #ccc' }}>
        <h2>Upload New Image-Text Pair</h2>
        <input type="file" accept="image/*" onChange={handleFileChange} />
        <br />
        <br />
        <input
          type="text"
          placeholder="Enter description"
          value={description}
          onChange={e => setDescription(e.target.value)}
          style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
        />
        <br />
        <br />
        <button onClick={handleUpload} style={{ padding: '8px 16px', cursor: 'pointer' }}>
          Upload
        </button>
      </div>

      <h1>Images</h1>
      
      {/* Gallery Grid */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
        {data.map(item => (
          <div key={item.id} style={{ border: '1px solid #ddd', padding: '10px', width: 'calc(33% - 20px)', boxSizing: 'border-box' }}>
            <img src={`${item.base64Image}`} alt={item.text} style={{ width: '100%', height: 'auto' }} />
            <p>{item.text}</p>
            <p>Human count: {item.humanCount}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default App;
