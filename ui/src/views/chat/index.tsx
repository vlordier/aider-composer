import ChatMessageList from './chatMessageList';
import ChatTextArea from './chatTextArea';

export function Chat() {
  return (
    <div
      style={{
        position: 'relative',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'flex-start',
        alignItems: 'stretch',
      }}
    >
      <ChatMessageList />
      <ChatTextArea />
    </div>
  );
}
