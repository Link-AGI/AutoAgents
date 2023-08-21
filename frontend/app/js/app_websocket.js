let apiKey;
let serpApiKey;
let ws = null;
let taskId = null;
let imageBaseDir = "../images/";

const apiHost = 'wss://demo.linksoul.ai/autoagents/api';
const apiHost = ((window.location.protocol === "https:") ? "wss://" : "ws://") + window.location.host + window.location.pathname + "api";

// Helpers
const sleep = (delay) => new Promise((resolve) => setTimeout(resolve, delay));
window.onload = async () => {
    await connect();
}

const getApiKey = document.getElementById('openai-api-key');
const getApiKeySerp = document.getElementById('serp-api-key');
getApiKey.addEventListener('input', () => {
    if (apiKey !== '' || apiKey !== undefined) {
        apiKey = getApiKey.value;
        console.log(apiKey);
    }
});
getApiKeySerp.addEventListener('input', () => {
    if (serpApiKey !== '' || serpApiKey !== undefined) {
        serpApiKey = getApiKeySerp.value;
        console.log(serpApiKey);
    }
});

function applyStyles(element) {
    element.style.backgroundColor = '#add8e6a8';
    element.style.padding = '12px';
    element.style.borderRadius = '1.2rem';
    element.style.marginTop = '30px !important';
}
function resetStyles(element) {
    element.style.backgroundColor = '';
    element.style.padding = '';
    element.style.borderRadius = '';
    element.style.marginTop = '';
}
function isEmpty(e) {
    if (e === undefined || e === null) {
        return true;
    }
    return false;
}
function profileImage(url) {
    const profileImage = document.createElement('img');
    profileImage.src = url;
    profileImage.height = 50;
    profileImage.width = 50;
    profileImage.className = 'agent-avatar';
    return profileImage;
}
function cleanResponseContent(content) {
    if (isEmpty(content)) { return; }

    // const contentWithoutHeadersOne = content.replace(/#\s+/g, '');
    const contentWithoutHeaders = content.replace(/##\s+/g, '');
    const cleanedContent = contentWithoutHeaders.replace(/"([^"]*)": ""\s*,?|{\s*}/g, '');
    const formattedContent = cleanedContent.replace(/\n/g, '<br>');
    const codeBlockRegex = /```([\s\S]*?)```/g;
    const formattedWithCodeBlocks = formattedContent.replace(codeBlockRegex, '<pre>$1</pre>');
    const codeSnippetRegex = /`([^`]+)`/g;
    const formattedFinal = formattedWithCodeBlocks.replace(codeSnippetRegex, '<code>$1</code>');
    return formattedFinal;
}

const imageFilenames = Array.from({ length: 20 }, (_, index) => `${index + 1}.jpg`);
let currentImageIndex = 0;

// Render agents on left col
function renderAgent(agent) {
    const agentsList = document.getElementById('agentsList');
    const listItem = document.createElement('li');
    const agentNameDiv = document.createElement('p');

    agentNameDiv.className = 'px-3 agents mt-3';
    agentsList.className = 'mt-4 py-3';
    listItem.className = 'list-group-item d-flex align-items-center';
    const agentName = agent.task_message.role;
    agentNameDiv.textContent = agentName;

    const agentProfileImage = currentImageIndex < imageFilenames.length
        ? `${imageBaseDir}${imageFilenames[currentImageIndex]}`
        : `${imageBaseDir}default.png`;

    currentImageIndex = (currentImageIndex + 1) % imageFilenames.length;

    const agentImage = profileImage(agentProfileImage);
    listItem.prepend(agentImage);

    listItem.appendChild(agentNameDiv);
    agentsList.appendChild(listItem);
}


// Scroll to msg of clicked step
let previousScrolledDiv = null;
function scrollToMessageDiv(agentRole) {
    const chatView = document.getElementById('chatView');
    const chatMessages = chatView.getElementsByClassName('chat-agent');

    for (const msgDiv of chatMessages) {
        if (msgDiv.getAttribute('data-role') === agentRole) {
            if (previousScrolledDiv) {
                resetStyles(previousScrolledDiv);
            }
            applyStyles(msgDiv);

            msgDiv.scrollIntoView({ behavior: 'smooth' });
            previousScrolledDiv = msgDiv;
            break;
        }
    }
}

// Render Lead agents responses
async function renderLeadAgentsResponses(responseData) {
    console.info(responseData);
    const chatView = document.getElementById('chatView');

    const chatMessages = responseData.filter((msg) => msg.task_message.role === "Question/Task" || msg.task_message.role === "Manager" || msg.task_message.role === "Agents Observer" || msg.task_message.role === "Plan Observer" || msg.task_message.role !== "" || msg.task_message.content !== "");

    chatMessages.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

    for (const msg of chatMessages) {
        const agentDiv = createAgentChatDiv(msg.task_message);
        chatView.appendChild(agentDiv);

        chatView.scrollTop = chatView.scrollHeight;
        clearCallingMessages();
    }
    showCallingNextAgentMessage();
    chatView.scrollTop = chatView.scrollHeight;
}

// Invite and render work agents
async function inviteTaskAgents(responseData) {
    console.info(responseData);
    const chatView = document.getElementById('chatView');
    const invitees = responseData.filter((msg) => msg.task_message.role === "Revised Role List");

    for (const agent of invitees) {
        const inviteMessageContainer = document.createElement('div');
        inviteMessageContainer.className = 'text-center invite-message fs';
        chatView.appendChild(inviteMessageContainer);

        for (const contentItem of agent.task_message.content) {
            const inviteMessage = document.createElement('p');
            inviteMessage.innerText = `Invited ${contentItem.name} to group chat`;
            inviteMessageContainer.appendChild(inviteMessage);
            chatView.scrollTop = chatView.scrollHeight;
            await sleep(1000);
        }
    }
}

// render task agents message
async function renderTaskAgentsResponse(responseData) {
    const chatView = document.getElementById('chatView');

    const namedAgents = responseData.filter((msg) => msg.task_message.role !== "Question/Task" && msg.task_message.role !== "Manager" && msg.task_message.role !== "Agents Observer" && msg.task_message.role !== "Plan Observer" && msg.task_message.role !== "" && msg.task_message.content !== "");
    // Render work agents responses
    for (const agent of namedAgents) {

        const agentChatMessages = responseData.filter((msg) => msg.task_message.role === agent.role);
        for (const msg of agentChatMessages) {
            const agentDiv = createAgentChatDiv(msg.task_message);
            chatView.appendChild(agentDiv);
            chatView.scrollTop = chatView.scrollHeight;
        }
    }
}

// Agent chat response divs
const renderedAgentMessage = {};
function createAgentChatDiv(msg) {
    const agentDiv = document.createElement('div');
    agentDiv.className = 'chat-agent d-flex';
    agentDiv.setAttribute('data-role', msg.role);

    const agentNameDiv = document.createElement('p');
    agentNameDiv.className = 'agent-name';

    const agentRole = msg.role;
    let agentCount = renderedAgentMessage.hasOwnProperty(agentRole) ? renderedAgentMessage[agentRole] + 1 : 1;
    renderedAgentMessage[agentRole] = agentCount;

    if (agentCount > 1) {
        agentNameDiv.textContent = `${agentRole}`;
    } else {
        agentNameDiv.textContent = agentRole;
    }

    const responseMessages = document.createElement('p');
    responseMessages.className = 'chat-bubble ms-2 px-3 pb-3';

    const agentProfileImage = currentImageIndex < imageFilenames.length
        ? `${imageBaseDir}${imageFilenames[currentImageIndex]}`
        : `${imageBaseDir}default.png`;

    const messageText = cleanResponseContent(msg.content);
    console.log(messageText);

    if (msg.role === 'Question/Task' || msg.role === 'Manager' || msg.role === 'Agents Observer' || msg.role === 'Plan Observer') {
        responseMessages.style.backgroundColor = 'rgb(170, 253, 217)';
    }

    if (!isEmpty(messageText) && messageText.length > 300) {
      const truncatedText = messageText.substring(0, 500);
      const fullText = messageText;
      const showMoreButton = document.createElement('button');
      showMoreButton.className = 'read-more mt-2 btn btn-success';
      showMoreButton.textContent = 'Show More';
      showMoreButton.addEventListener('click', function() {
          showFullText(this);
      });

      responseMessages.innerHTML = `${truncatedText}`;
      responseMessages.appendChild(showMoreButton);
      responseMessages.prepend(agentNameDiv);
      responseMessages.dataset.fullText = fullText;
    } else {
        responseMessages.innerHTML = messageText;
    }
    chatView.scrollTop = chatView.scrollHeight;

    const agentImage = profileImage(agentProfileImage);
    agentDiv.prepend(agentImage);
    responseMessages.prepend(agentNameDiv);
    agentDiv.appendChild(responseMessages);
    return agentDiv;
}


let callingMessageCount = 0;
let callingMessageInterval = null;

function clearCallingMessages() {
  const chatView = document.getElementById('chatView');
  const callingMessages = chatView.querySelectorAll('.calling-message');
  callingMessages.forEach((message) => {
      chatView.removeChild(message);
  });
  clearInterval(callingMessageInterval);
}

function showCallingNextAgentMessage() {
  const chatView = document.getElementById('chatView');
  const callingMessage = document.createElement('p');
  callingMessage.className = 'calling-message fs';
  callingMessage.textContent = 'Calling next agent';
  callingMessage.dataset.messageId = callingMessageCount;
  chatView.appendChild(callingMessage);
  callingMessageCount++;

  const animationFrames = ['Calling', 'Calling next', 'Calling next agent..', 'Calling next agent...'];
  let frameIndex = 0;

  const updateMessage = () => {
      callingMessage.textContent = animationFrames[frameIndex];
      frameIndex = (frameIndex + 1) % animationFrames.length;
  };
  callingMessageInterval = setInterval(updateMessage, 500);

  return {
      stop: () => {
          if (callingMessage.dataset.messageId == callingMessageCount - 1) {
              callingMessage.style.display = 'none';
          }
          clearInterval(callingMessageInterval);
          chatView.removeChild(callingMessage);
      }
  };
}

function showFullText(element) {
    const parentMessage = element.parentElement;
    const fullText = parentMessage.dataset.fullText;
    const fullTextParagraph = document.createElement('p');
    const agentNameDiv = parentMessage.querySelector('.agent-name'); 
    fullTextParagraph.innerHTML = fullText;
    const foldButton = document.createElement('button');
    foldButton.className = 'read-more mt-2 btn btn-success';
    foldButton.textContent = 'Show less';
    foldButton.addEventListener('click', function() {
        hideFullText(this);
    });
    parentMessage.innerHTML = ''; 
    parentMessage.prepend(agentNameDiv);
    parentMessage.appendChild(fullTextParagraph);
    parentMessage.appendChild(foldButton);
}
  
function hideFullText(element) {
    const parentMessage = element.parentElement;
    const truncatedText = parentMessage.dataset.fullText.substring(0, 500);
    const agentNameDiv = parentMessage.querySelector('.agent-name'); 
    const truncatedTextParagraph = document.createElement('p');
    truncatedTextParagraph.innerHTML = truncatedText;
    const showMoreButton = document.createElement('button');
    showMoreButton.className = 'read-more mt-2 btn btn-success';
    showMoreButton.textContent = 'Show More';
    showMoreButton.addEventListener('click', function() {
        showFullText(this);
    });
    parentMessage.innerHTML = ''; 
    parentMessage.prepend(agentNameDiv);
    parentMessage.appendChild(truncatedTextParagraph);
    parentMessage.appendChild(showMoreButton);
}

// Render tasks in the right column
async function displayTasks(responseData) {
    console.info(responseData);
    const taskView = document.getElementById('taskView');

    // tasks and their progress
    responseData.forEach((task) => {
        if (task.task_message.role === 'Question/Task') {
            const taskItem = document.createElement('div');
            taskItem.className = 'alert alert-primary fw-bold';
            taskItem.textContent = task.task_message.content;
            taskView.appendChild(taskItem);
        }
    });
}
function styleSelectedStep(item) {
    const allListItems = document.querySelectorAll('.task-step');
    allListItems.forEach((listItem) => {
        listItem.style.border = "none";
        listItem.style.backgroundColor = "#fff";
    });
    item.style.backgroundColor = "#add8e6a8";
    item.style.borderRadius = "1.3rem";
}

const renderedLeadAgents = {};
async function renderLeadAgents(responseData) {
    console.info(responseData);

    const leadAgents = responseData.filter((msg) => msg.task_message.role === "Question/Task" || msg.task_message.role === "Manager" || msg.task_message.role === "Agents Observer" || msg.task_message.role === "Plan Observer" || msg.task_message.role !== "" || msg.task_message.content !== "");

    for (const agent of leadAgents) {
        const agentRole = agent.task_message.role;
        if (!renderedLeadAgents.hasOwnProperty(agentRole)) {
            renderedLeadAgents[agentRole] = true;
            renderAgent(agent);
        }
    }
}
// Render task(s) and progress
const renderedTasks = {};
let taskStepCount = 0; 
async function displayTaskSteps(responseData) {
    console.info(responseData);
    const taskView = document.getElementById('taskView');

    let completedStages = 0;
    // Progress bar
    const progressBar = document.createElement('div');
    progressBar.className = 'progress-bar';

    for (let i = 0; i < responseData.length; i++) {
        const step = responseData[i];

        if (step.task_message.role) {
            const agentRole = step.task_message.role;
            if (renderedTasks.hasOwnProperty(agentRole)) {
                renderedTasks[agentRole] = true;
            }

            const stepItem = document.createElement('div');
            stepItem.className = 'task-step';

            stepItem.addEventListener('click', () => {
                scrollToMessageDiv(step.task_message.role);
                styleSelectedStep(stepItem);
            });

            // Expert details
            const expertDetails = document.createElement('div');
            expertDetails.className = 'expert-details d-flex';

            // Use the taskStepCount to set the step number
            const stepNumber = document.createElement('div');
            stepNumber.className = 'step-number';
            stepNumber.textContent = ++taskStepCount; // Increment and assign

            const expertNameContent = renderedTasks[agentRole] > 1
                ? `${agentRole}`
                : agentRole;

            expertDetails.innerHTML = `
                <div class="step-content ms-3">
                    <div class="expert-name fw-bold">${expertNameContent}</div>
                    <p class="status">Pending...</p>
                </div>
            `;

            expertDetails.insertBefore(stepNumber, expertDetails.firstChild);

            stepItem.appendChild(expertDetails);
            stepItem.appendChild(progressBar);
            taskView.appendChild(stepItem);
        }
    }
    // Animate progress bar
    const expertName = document.querySelectorAll('.expert-name');
    const status = document.querySelectorAll('.status');
    const stepNumberElements = taskView.querySelectorAll('.step-number');

    for (let i = 0; i <= completedStages; i++) {
        stepNumberElements[i].classList.add('step-number-completed');
        expertName[i].classList.add('completed');
        status[i].textContent = 'Completed task(s)';
        status[i].classList.add('completed');
        if (i < stepNumberElements.length - 1) {
          completedStages++;
        }
    }
    progressBar.classList.add('completed-stage');
}

// Disable buttons if no input or api keys
const sendButton = document.getElementById('sendButton');
const sendIput = document.getElementById('inputMessage');
sendButton.disabled = true;
sendButton.style.color = '#9d9d9d';

function sendBtn() {
    if (sendIput.value.trim() !== '') {
        sendButton.disabled = false;
        sendButton.style.color = '#079f49';
    } else {
        sendButton.disabled = true;
        sendButton.style.color = '#9d9d9d';
    }
}
sendIput.addEventListener('input', sendBtn);
sendBtn();

// handle sending messages in the chat
async function sendMessage(exampleMessage) {
    const apiKey = document.getElementById('openai-api-key').value;
    const serpApiKey = document.getElementById('serp-api-key').value;
    const exampleMessagesID = document.getElementById("example-messages");
    const intro = document.querySelector('.intro');

    const sentMessage = document.getElementById('inputMessage').value;
    const inputMessage = sentMessage || exampleMessage;


    if (ws == null || ws.readyState != 1) {
        await connect();
        await sleep(800);
    }

    if ((!apiKey || apiKey.trim() === '' || apiKey === undefined) && (!serpApiKey || serpApiKey.trim() === '' || serpApiKey === undefined)) {
        alert('Please enter both API keys');
    } else if (inputMessage === '') {
        alert('Please enter a message');
    } else {
        localStorage.setItem("llm_api_key", apiKey.trim());
        localStorage.setItem("serpapi_key", serpApiKey.trim());
        // Get the input message and render into chat
        const chatView = document.getElementById('chatView');

        const messageDiv = document.createElement('div');

        const sentMesage = document.createElement('p');
        sentMesage.className = 'chat-bubble me-2 p-3';
        sentMesage.textContent = inputMessage;

        const senderImage = document.createElement('img');
        senderImage.src = '../images/default.jpg';
        senderImage.height = 50;
        senderImage.width = 50;
        senderImage.className = 'agent-avatar';

        messageDiv.className = 'chat-user d-flex mb-2 mt-5 justify-content-end';
        messageDiv.appendChild(sentMesage);
        messageDiv.appendChild(senderImage);
        chatView.appendChild(messageDiv);

        ws.send(JSON.stringify({
            "action": "run_task",
            "data": {
                "llm_api_key": apiKey,
                "serpapi_key": serpApiKey,
                "idea": inputMessage
            }
        }));

        // Clear the input field
        document.getElementById('inputMessage').value = '';
        intro.style.display = 'none';
        exampleMessagesID.style.display = 'none';

        // show Stop button
        const interruptButton = document.createElement('button');
        const callingMessages = document.querySelectorAll("calling-message");

        interruptButton.textContent = 'Stop';
        interruptButton.id = 'interruptButton';
        interruptButton.classList.add('btn', 'btn-primary', 'mb-3');
        interruptButton.addEventListener('click', async () => {
            clearCallingMessages();
            if (taskId != null) {
                ws.send(JSON.stringify({
                    "action": "interrupt",
                    "data": {
                        "task_id": taskId
                    }
                }));
            }
            interruptButton.style.color = 'red';
            interruptButton.textContent = 'Stopped';
            
            callingMessages.forEach((callingMessage) => {
                callingMessage.style.display = "none !important";
            })
        });
        chatView.appendChild(interruptButton);
    }
}

// Add event listener to send button
document.getElementById('sendButton').addEventListener('click', sendMessage);
document.getElementById('inputMessage').addEventListener('keydown', function(e){
    if(e.key == "Enter"){
        sendMessage();
    }
})

document.addEventListener("DOMContentLoaded", function () {
    const exampleInputs = document.querySelectorAll(".example-input");
    exampleInputs.forEach(function (example) {
        // if (ws = null){ example.disabled = true;}
        example.addEventListener("click", function () {
            const inputValue = example.getAttribute("data-input");
            sendMessage(inputValue);
        });
    });
});

// Websocket connection
async function connect() {
    ws = new WebSocket(apiHost);
    ws.onopen = function (e) {
        console.log('ws opened');
        if (ws.readyState == 1) {
            console.log('ws connected');
        }
    };

    ws.onmessage = async function (e) {
        console.log(e['data'])
        var response = JSON.parse(e['data']);
        if (response["action"] == "run_task") {
            console.log(response);
            // nothing to do
            if (response['msg'] == 'ok') {
                taskId = response['data']['task_id'];
                console.log(response["data"])
                let responseData = [response["data"]];
                // data rendering fxns
                await renderLeadAgentsResponses(responseData).then(inviteTaskAgents(responseData));
                await renderTaskAgentsResponse(responseData);
                await renderLeadAgents(responseData);
                await displayTasks(responseData);
                await displayTaskSteps(responseData);
            } else if (response['msg'] == 'finished') {
                clearCallingMessages();
                console.log("task: " + taskId + " finished.");
                taskId = null;

                const clearButton = document.createElement('button');
                const stoppedMessage = document.getElementById('interruptButton');
                stoppedMessage.textContent = 'Finished';
                stoppedMessage.style.color = 'green';
                
                clearButton.textContent = 'Clear';
                clearButton.id = "clearButton";
                clearButton.classList.add('btn', 'btn-primary', 'mb-3');
                
                clearButton.addEventListener('click', async () => {
                   window.location.reload();
                // clearChat();
                });
                const chatView = document.getElementById('chatView');
                chatView.appendChild(clearButton);
            } else {
                // errors
                console.log(response['msg']);
                taskId = null;
            }
        }

        if (response['action'] == "interrupt") {
            clearCallingMessages();
            if (response['msg'] == 'ok') {
                console.log("task: " + taskId + " interrupted.");
                taskId = null;
                const interruptMessage = document.getElementById("interruptButton");
                interruptMessage.textContent = 'Stopped';
                interruptMessage.style.color = 'red';
            }
        }
    }
    ws.onerror = function (err) {
        console.info('ws error: ' + err)
    }

    ws.onclose = function (e) {
        console.info('ws close: ' + e);
    };
}

document.addEventListener('DOMContentLoaded', function () {
    var toggleLeftBtn = document.getElementById('toggleLeft');
    var toggleRightBtn = document.getElementById('toggleRight');
    var colLeft = document.querySelector('.col-left');
    var colRight = document.querySelector('.col-right');

    toggleLeftBtn.addEventListener('click', function () {
        colLeft.classList.toggle('show');
        colLeft.style.transition = 'all 0.3s ease-in-out !important';
        colRight.classList.remove('show');
    });

    toggleRightBtn.addEventListener('click', function () {
        colRight.classList.toggle('show');
        colLeft.classList.remove('show');
    });

    let apiKey = localStorage.getItem("llm_api_key");
    let serpApiKey = localStorage.getItem("serpapi_key");
    if(apiKey) {
        document.getElementById('openai-api-key').value = apiKey;
        localStorage.removeItem('llm_api_key');
    }
    if(serpApiKey) {
        document.getElementById('serp-api-key').value = serpApiKey;
        localStorage.removeItem('serpapi_key');
    }
});
