import React, { useState } from 'react';
import styled from 'styled-components';
import { 
  User, 
  Mail, 
  Edit3, 
  Save, 
  X, 
  Plus, 
  Trash2,
  Palette,
  Heart,
  Smile
} from 'lucide-react';
import { useUser } from '../contexts/UserContext';
import LoadingSpinner from './LoadingSpinner';
import toast from 'react-hot-toast';

const ProfileContainer = styled.div`
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
`;

const ProfileCard = styled.div`
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 2rem;
  margin-bottom: 2rem;
`;

const SectionTitle = styled.h2`
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const ProfileHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 2rem;
  margin-bottom: 2rem;
`;

const Avatar = styled.div`
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 2rem;
  font-weight: bold;
`;

const UserInfo = styled.div`
  flex: 1;
`;

const UserName = styled.h1`
  font-size: 2rem;
  font-weight: bold;
  color: #333;
  margin-bottom: 0.5rem;
`;

const UserEmail = styled.p`
  color: #666;
  font-size: 1.1rem;
  margin-bottom: 1rem;
`;

const EditButton = styled.button`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s ease;

  &:hover {
    background: #5a67d8;
  }
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
`;

const Label = styled.label`
  font-weight: 600;
  color: #333;
`;

const Input = styled.input`
  padding: 0.75rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s ease;

  &:focus {
    outline: none;
    border-color: #667eea;
  }
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
`;

const Button = styled.button`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;

  ${props => props.$variant === 'primary' ? `
    background: #667eea;
    color: white;
    &:hover { background: #5a67d8; }
  ` : `
    background: #e2e8f0;
    color: #666;
    &:hover { background: #cbd5e0; }
  `}
`;

const PreferenceSection = styled.div`
  margin-top: 2rem;
`;

const PreferenceGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
`;

const PreferenceCard = styled.div`
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const PreferenceInfo = styled.div`
  flex: 1;
`;

const PreferenceType = styled.div`
  font-size: 0.8rem;
  color: #666;
  text-transform: uppercase;
  font-weight: 600;
`;

const PreferenceValue = styled.div`
  font-weight: 600;
  color: #333;
  margin-top: 0.2rem;
`;

const PreferenceWeight = styled.div`
  font-size: 0.8rem;
  color: #667eea;
  margin-top: 0.2rem;
`;

const DeleteButton = styled.button`
  background: none;
  border: none;
  color: #ef4444;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: background 0.2s ease;

  &:hover {
    background: rgba(239, 68, 68, 0.1);
  }
`;

const AddPreferenceForm = styled.div`
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1rem;
  display: grid;
  grid-template-columns: 1fr 1fr 1fr auto;
  gap: 1rem;
  align-items: end;
`;

const MoodSection = styled.div`
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1rem;
  margin-top: 1rem;
`;

const MoodForm = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr 2fr auto;
  gap: 1rem;
  align-items: end;
`;

const Select = styled.select`
  padding: 0.75rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 1rem;
  background: white;
  transition: border-color 0.2s ease;

  &:focus {
    outline: none;
    border-color: #667eea;
  }
`;

const Profile = () => {
  const { user, loading, preferences, currentMood, updateProfile, addPreference, removePreference, updateMood } = useUser();
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    username: '',
    first_name: '',
    last_name: ''
  });
  const [newPreference, setNewPreference] = useState({
    type: 'color',
    value: '',
    weight: 1.0
  });
  const [newMood, setNewMood] = useState({
    mood: 'happy',
    intensity: 'medium',
    context: ''
  });

  React.useEffect(() => {
    if (user) {
      setFormData({
        username: user.username || '',
        first_name: user.first_name || '',
        last_name: user.last_name || ''
      });
    }
  }, [user]);

  if (loading) {
    return <LoadingSpinner />;
  }

  const handleEditToggle = () => {
    setIsEditing(!isEditing);
    if (!isEditing && user) {
      setFormData({
        username: user.username || '',
        first_name: user.first_name || '',
        last_name: user.last_name || ''
      });
    }
  };

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    try {
      await updateProfile(formData);
      setIsEditing(false);
    } catch (error) {
      console.error('Profile update failed:', error);
    }
  };

  const handleAddPreference = async (e) => {
    e.preventDefault();
    if (!newPreference.value.trim()) {
      toast.error('请输入偏好值');
      return;
    }
    
    try {
      await addPreference(newPreference);
      setNewPreference({ type: 'color', value: '', weight: 1.0 });
    } catch (error) {
      console.error('Add preference failed:', error);
    }
  };

  const handleRemovePreference = async (type, value) => {
    try {
      await removePreference(type, value);
    } catch (error) {
      console.error('Remove preference failed:', error);
    }
  };

  const handleUpdateMood = async (e) => {
    e.preventDefault();
    if (!newMood.context.trim()) {
      toast.error('请描述一下您的心情');
      return;
    }
    
    try {
      await updateMood(newMood);
      setNewMood({ mood: 'happy', intensity: 'medium', context: '' });
    } catch (error) {
      console.error('Update mood failed:', error);
    }
  };

  const getInitials = (firstName, lastName, email) => {
    if (firstName && lastName) {
      return `${firstName[0]}${lastName[0]}`.toUpperCase();
    }
    if (firstName) {
      return firstName[0].toUpperCase();
    }
    if (email) {
      return email[0].toUpperCase();
    }
    return 'U';
  };

  return (
    <ProfileContainer>
      <ProfileCard>
        <SectionTitle>
          <User size={24} />
          个人资料
        </SectionTitle>
        
        <ProfileHeader>
          <Avatar>
            {getInitials(user?.first_name, user?.last_name, user?.email)}
          </Avatar>
          <UserInfo>
            <UserName>
              {user?.first_name && user?.last_name 
                ? `${user.first_name} ${user.last_name}`
                : user?.username || '未设置姓名'
              }
            </UserName>
            <UserEmail>
              <Mail size={16} style={{ marginRight: '0.5rem' }} />
              {user?.email}
            </UserEmail>
            <EditButton onClick={handleEditToggle}>
              {isEditing ? <X size={16} /> : <Edit3 size={16} />}
              {isEditing ? '取消' : '编辑资料'}
            </EditButton>
          </UserInfo>
        </ProfileHeader>

        {isEditing ? (
          <Form onSubmit={handleSaveProfile}>
            <FormGroup>
              <Label>用户名</Label>
              <Input
                type="text"
                value={formData.username}
                onChange={(e) => setFormData({...formData, username: e.target.value})}
                placeholder="输入用户名"
              />
            </FormGroup>
            <FormGroup>
              <Label>名字</Label>
              <Input
                type="text"
                value={formData.first_name}
                onChange={(e) => setFormData({...formData, first_name: e.target.value})}
                placeholder="输入名字"
              />
            </FormGroup>
            <FormGroup>
              <Label>姓氏</Label>
              <Input
                type="text"
                value={formData.last_name}
                onChange={(e) => setFormData({...formData, last_name: e.target.value})}
                placeholder="输入姓氏"
              />
            </FormGroup>
            <ButtonGroup>
              <Button type="button" onClick={handleEditToggle}>
                <X size={16} />
                取消
              </Button>
              <Button type="submit" $variant="primary">
                <Save size={16} />
                保存
              </Button>
            </ButtonGroup>
          </Form>
        ) : null}
      </ProfileCard>

      <ProfileCard>
        <SectionTitle>
          <Palette size={24} />
          艺术偏好
        </SectionTitle>
        
        <PreferenceGrid>
          {preferences?.map((pref, index) => (
            <PreferenceCard key={index}>
              <PreferenceInfo>
                <PreferenceType>{pref.type}</PreferenceType>
                <PreferenceValue>{pref.value}</PreferenceValue>
                <PreferenceWeight>权重: {pref.weight}</PreferenceWeight>
              </PreferenceInfo>
              <DeleteButton onClick={() => handleRemovePreference(pref.type, pref.value)}>
                <Trash2 size={16} />
              </DeleteButton>
            </PreferenceCard>
          ))}
        </PreferenceGrid>

        <AddPreferenceForm>
          <FormGroup>
            <Label>类型</Label>
            <Select
              value={newPreference.type}
              onChange={(e) => setNewPreference({...newPreference, type: e.target.value})}
            >
              <option value="color">颜色</option>
              <option value="theme">主题</option>
              <option value="style">风格</option>
              <option value="artist">艺术家</option>
            </Select>
          </FormGroup>
          <FormGroup>
            <Label>偏好值</Label>
            <Input
              type="text"
              value={newPreference.value}
              onChange={(e) => setNewPreference({...newPreference, value: e.target.value})}
              placeholder="例如: 蓝色, 印象派"
            />
          </FormGroup>
          <FormGroup>
            <Label>权重 (0-1)</Label>
            <Input
              type="number"
              min="0"
              max="1"
              step="0.1"
              value={newPreference.weight}
              onChange={(e) => setNewPreference({...newPreference, weight: parseFloat(e.target.value)})}
            />
          </FormGroup>
          <Button type="button" $variant="primary" onClick={handleAddPreference}>
            <Plus size={16} />
            添加
          </Button>
        </AddPreferenceForm>
      </ProfileCard>

      <ProfileCard>
        <SectionTitle>
          <Smile size={24} />
          当前心情
        </SectionTitle>
        
        {currentMood && (
          <div style={{ marginBottom: '1rem', padding: '1rem', background: '#f8f9fa', borderRadius: '8px' }}>
            <strong>当前心情:</strong> {currentMood.mood} ({currentMood.intensity})
            {currentMood.context && <div style={{ marginTop: '0.5rem', color: '#666' }}>{currentMood.context}</div>}
          </div>
        )}

        <MoodSection>
          <MoodForm>
            <FormGroup>
              <Label>心情</Label>
              <Select
                value={newMood.mood}
                onChange={(e) => setNewMood({...newMood, mood: e.target.value})}
              >
                <option value="happy">开心</option>
                <option value="sad">悲伤</option>
                <option value="excited">兴奋</option>
                <option value="calm">平静</option>
                <option value="anxious">焦虑</option>
                <option value="angry">愤怒</option>
                <option value="content">满足</option>
                <option value="lonely">孤独</option>
              </Select>
            </FormGroup>
            <FormGroup>
              <Label>强度</Label>
              <Select
                value={newMood.intensity}
                onChange={(e) => setNewMood({...newMood, intensity: e.target.value})}
              >
                <option value="low">轻微</option>
                <option value="medium">一般</option>
                <option value="high">强烈</option>
              </Select>
            </FormGroup>
            <FormGroup>
              <Label>描述</Label>
              <Input
                type="text"
                value={newMood.context}
                onChange={(e) => setNewMood({...newMood, context: e.target.value})}
                placeholder="描述一下您现在的感受..."
              />
            </FormGroup>
            <Button type="button" $variant="primary" onClick={handleUpdateMood}>
              <Heart size={16} />
              更新
            </Button>
          </MoodForm>
        </MoodSection>
      </ProfileCard>
    </ProfileContainer>
  );
};

export default Profile;
