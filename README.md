# chefgpt

# Deployment (AWS)

## Compute Choice (Fargate):

The simplicity of this application doesn’t warrant the fine control offered by an EC2 and EKS.
Lambda increases latency due to cold starts (if each function was a graph).
Fargate is the best choice since it abstracts the complexity of managing the infrastructure. Additionally, Fargate tasks are easy to set up with containers and they can be scaled automatically.

## Secret Management

Parameter Store is appropriate given the simplicity of this application. There’s only two API keys that need to be injected at runtime. Secrets Manager is more in-depth allowing key rotation and adding policies to the secrets. In the near future, especially if databases were added (higher risk), Secrets Manager would be worth the cost tradeoff and slight increase in complexity.

## Observability

Application/Container: JSON logging within the backend container itself. The structure of the log could look something like:
`{ request_id, user_id, latency, error }`
And send the logs to AWS CloudWatch which can capture the output of these containers running on ECS Fargate.
Additionally could add alarms on CloudWatch for specific triggers, like p99 latency, server error rates, etc.
Infrastructure: Eventually, add X-Ray to view the latency of end-to-end flow and time spent at each point of the flow (load balancer, API, etc). But not necessary at low scale.
LLM: LangSmith to see the metrics and latency of the agent themselves. Easier to debug prompts/flows, measure performance, and track costs. (time-to-first token, latency, output quality/datasets, regression testing).
