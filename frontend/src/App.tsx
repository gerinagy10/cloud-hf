// App.tsx

import React, { useEffect, useState } from 'react';

interface ImageTextPair {
  id: string;
  imageUrl: string;
  text: string;
}

const App: React.FC = () => {
  const [data, setData] = useState<ImageTextPair[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [description, setDescription] = useState('');

  // Fetch image-text pairs from the API on component mount
  useEffect(() => {
    fetchData();
  }, []);

  // Function to get data from our API endpoint
  const fetchData = async () => {
    try {
      // const response = await fetch('/api/image-text');
      // if (!response.ok) {
      //   throw new Error('Network response was not ok');
      // }
      // const result: ImageTextPair[] = await response.json();

      setData(sampleData);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  // Handle file input change event
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  // Handle form submission to upload a new image-text pair
  const handleUpload = async () => {
    if (!selectedFile || !description) {
      return;
    }

    const formData = new FormData();
    formData.append('image', selectedFile);
    formData.append('text', description);

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) {
        throw new Error('Upload failed');
      }
      // Clear the inputs and refresh the data after successful upload
      setSelectedFile(null);
      setDescription('');
      fetchData();
    } catch (error) {
      console.error('Error uploading:', error);
    }
  };

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
            <img src={item.imageUrl} alt={item.text} style={{ width: '100%', height: 'auto' }} />
            <p>{item.text}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

const sampleData: ImageTextPair[] = [
  {
    id: "1",
    imageUrl: "https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fblog.shareaholic.com%2Fwp-content%2Fuploads%2F2012%2F06%2Fcrowd-of-people.jpg&f=1&nofb=1&ipt=ee265022fe4caf6b7a99bc636cd9e13fadda96de825a22fa47be48c6a1def2a9",
    text: "A beautiful sunset over the mountains.",
  },
  {
    id: "2",
    imageUrl: "https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fblog.shareaholic.com%2Fwp-content%2Fuploads%2F2012%2F06%2Fcrowd-of-people.jpg&f=1&nofb=1&ipt=ee265022fe4caf6b7a99bc636cd9e13fadda96de825a22fa47be48c6a1def2a9",
    text: "Relaxing day at the beach with palm trees.",
  },
  {
    id: "3",
    imageUrl: "https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fblog.shareaholic.com%2Fwp-content%2Fuploads%2F2012%2F06%2Fcrowd-of-people.jpg&f=1&nofb=1&ipt=ee265022fe4caf6b7a99bc636cd9e13fadda96de825a22fa47be48c6a1def2a9",
    text: "A bustling city skyline at night.",
  },
  {
    id: "4",
    imageUrl: "https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fblog.shareaholic.com%2Fwp-content%2Fuploads%2F2012%2F06%2Fcrowd-of-people.jpg&f=1&nofb=1&ipt=ee265022fe4caf6b7a99bc636cd9e13fadda96de825a22fa47be48c6a1def2a9",
    text: "A quiet forest trail in autumn.",
  },
  {
    id: "5",
    imageUrl: "https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fblog.shareaholic.com%2Fwp-content%2Fuploads%2F2012%2F06%2Fcrowd-of-people.jpg&f=1&nofb=1&ipt=ee265022fe4caf6b7a99bc636cd9e13fadda96de825a22fa47be48c6a1def2a9",
    text: "A glimpse into the stars and galaxies.",
  },
];

export default App;
