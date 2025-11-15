import json
import aiohttp
from botbuilder.core import MessageFactory, UserState
from botbuilder.dialogs import ComponentDialog, WaterfallDialog, WaterfallStepContext, DialogTurnResult
from botbuilder.dialogs.prompts import TextPrompt, PromptOptions, ChoicePrompt, DateTimePrompt
from botbuilder.dialogs.choices import Choice, ListStyle
from config import DefaultConfig

CONFIG = DefaultConfig()

class ReservarHotelDialog(ComponentDialog):
    def __init__(self, user_state: UserState):
        super(ReservarHotelDialog, self).__init__("ReservarHotelDialog")
        
        # Guarda na memória onde o usuário parou no diálogo
        self.user_state = user_state
        
        # Adiciona prompts necessários
        self.add_dialog(TextPrompt(TextPrompt.__name__))
        
        # Configurando o ChoicePrompt para usar botões por padrão
        choice_prompt = ChoicePrompt(ChoicePrompt.__name__)
        choice_prompt.style = ListStyle.suggested_action
        self.add_dialog(choice_prompt)
        
        self.add_dialog(DateTimePrompt(DateTimePrompt.__name__))
        
        # Conversação Sequencial (Steps)        
        self.add_dialog(
            WaterfallDialog(
                "ReservarHotelDialog",
                [
                    self.prompt_nome_step,
                    self.prompt_email_step,
                    self.prompt_celular_step,
                    self.prompt_cpf_step,
                    self.prompt_cidade_step,
                    self.prompt_hotel_step,
                    self.prompt_data_entrada_step,
                    self.prompt_data_saida_step,
                    self.confirmar_reserva_step,
                    self.processar_reserva_step,
                    self.final_step
                ]
            )
        )
                
        self.initial_dialog_id = "ReservarHotelDialog"
    
    async def prompt_nome_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        await step_context.context.send_activity(MessageFactory.text("Vamos realizar sua reserva de hotel!"))
        
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text("Por favor, informe seu nome completo:"))
        )
    
    async def prompt_email_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["nome"] = step_context.result
        
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text("Informe seu email para contato:"))
        )
    
    async def prompt_celular_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["email"] = step_context.result
        
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text("Informe seu número de celular (ex: 21999998888):"))
        )
    
    async def prompt_cpf_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["celular"] = step_context.result
        
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text("Informe seu CPF (apenas números):"))
        )
    
    async def prompt_cidade_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["cpf"] = step_context.result
        
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text("Para qual cidade você deseja viajar?"))
        )
    
    async def prompt_hotel_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        cidade = step_context.result
        step_context.values["cidade_nome"] = cidade

        # Buscar o código da cidade
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{CONFIG.API_BASE_URL}/hotels/searchByCity?destinationCity={cidade}") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and data.get('data'):
                            city_code = data['data'][0]['iataCode']
                            step_context.values["cidade"] = city_code
                            
                            # Buscar hotéis na cidade
                            async with session.get(f"{CONFIG.API_BASE_URL}/hotels/searchHotelsByCityCode?cityCode={city_code}") as response_hotels:
                                if response_hotels.status == 200:
                                    hotels_data = await response_hotels.json()
                                    if hotels_data and hotels_data.get('data'):
                                        hoteis = [f"{hotel['hotel']['name']} ({hotel['hotel']['hotelId']})" for hotel in hotels_data['data']]
                                        options = [Choice(value=hotel) for hotel in hoteis]
                                        return await step_context.prompt(
                                            ChoicePrompt.__name__,
                                            PromptOptions(
                                                prompt=MessageFactory.text(f"Qual hotel em {cidade} você deseja reservar?"),
                                                choices=options,
                                                style=ListStyle.suggested_action
                                            )
                                        )
                        await step_context.context.send_activity(MessageFactory.text(f"Não encontrei hotéis para a cidade {cidade}."))
                        return await step_context.end_dialog()
                    else:
                        await step_context.context.send_activity(MessageFactory.text("Não consegui buscar os hotéis. Tente novamente."))
                        return await step_context.end_dialog()
        except Exception:
            await step_context.context.send_activity(MessageFactory.text("Ocorreu um erro ao buscar os hotéis."))
            return await step_context.end_dialog()
    
    async def prompt_data_entrada_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        hotel_selection = step_context.result.value
        hotel_id = hotel_selection.split('(')[-1].replace(')', '')
        hotel_name = hotel_selection.split(' (')[0]
        step_context.values["hotel"] = hotel_name
        step_context.values["hotel_id"] = hotel_id
        
        await step_context.context.send_activity(
            MessageFactory.text("Para a data de entrada, informe no formato DD/MM/AAAA (exemplo: 15/11/2025)")
        )
        
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text("Data de check-in:"))
        )
    
    async def prompt_data_saida_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["data_entrada"] = step_context.result
        
        await step_context.context.send_activity(
            MessageFactory.text("Para a data de saída, informe no formato DD/MM/AAAA (exemplo: 20/11/2025)")
        )
        
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text("Data de check-out:"))
        )
    
    async def confirmar_reserva_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        step_context.values["data_saida"] = step_context.result
        
        resumo = (
            f"**Resumo da reserva:**\n\n"
            f"**Nome:** {step_context.values['nome']}\n"
            f"**Email:** {step_context.values['email']}\n"
            f"**Celular:** {step_context.values['celular']}\n"
            f"**CPF:** {step_context.values['cpf']}\n"
            f"**Cidade:** {step_context.values['cidade_nome']}\n"
            f"**Hotel:** {step_context.values['hotel']}\n"
            f"**Check-in:** {step_context.values['data_entrada']}\n"
            f"**Check-out:** {step_context.values['data_saida']}\n\n"
            f"Confirma a reserva?"
        )
        
        return await step_context.prompt(
            ChoicePrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text(resumo),
                choices=[Choice("Sim"), Choice("Não")],
                style=ListStyle.suggested_action
            )
        )
    
    async def processar_reserva_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if step_context.result.value == "Sim":
            # Transformar as datas para o formato correto
            try:
                data_entrada_parts = step_context.values["data_entrada"].split("/")
                data_saida_parts = step_context.values["data_saida"].split("/")
                
                data_entrada_iso = f"{data_entrada_parts[2]}-{data_entrada_parts[1]}-{data_entrada_parts[0]}"
                data_saida_iso = f"{data_saida_parts[2]}-{data_saida_parts[1]}-{data_saida_parts[0]}"
                
                # Criar o payload para a API
                payload = {
                    "cliente": {
                        "nome": step_context.values["nome"],
                        "email": step_context.values["email"],
                        "celular": step_context.values["celular"],
                        "cpf": step_context.values["cpf"]
                    },
                    "cidade": step_context.values["cidade"],
                    "hotel": step_context.values["hotel"],
                    "dataEntrada": data_entrada_iso,
                    "dataSaida": data_saida_iso
                }
                
                # Enviar para a API
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            f"{CONFIG.API_BASE_URL}/reservas-hotel", 
                            json=payload,
                            headers={"Content-Type": "application/json"}
                        ) as response:
                            if response.status in [200, 201]:
                                await step_context.context.send_activity(
                                    MessageFactory.text("✅ Sua reserva de hotel foi confirmada com sucesso! Em breve você receberá um e-mail com os detalhes.")
                                )
                            else:
                                await step_context.context.send_activity(
                                    MessageFactory.text(f"❌ Houve um problema ao confirmar sua reserva. Por favor, tente novamente mais tarde. (Erro: {response.status})")
                                )
                except Exception:
                    await step_context.context.send_activity(
                        MessageFactory.text("❌ Não foi possível conectar com nosso sistema de reservas. Por favor, tente novamente mais tarde.")
                    )
            except Exception:
                await step_context.context.send_activity(
                    MessageFactory.text("❌ Formato de data inválido. Por favor, tente fazer a reserva novamente.")
                )
        else:
            await step_context.context.send_activity(MessageFactory.text("Reserva cancelada."))
        
        # Perguntar se deseja fazer algo mais
        return await step_context.prompt(
            ChoicePrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text("O que você gostaria de fazer agora?"),
                choices=[Choice("Voltar ao menu principal"), Choice("Fazer outra reserva de hotel")],
                style=ListStyle.suggested_action
            )
        )
    
    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        escolha = step_context.result.value
        
        if escolha == "Fazer outra reserva de hotel":
            return await step_context.replace_dialog(self.id)
        
        # Voltar para o menu principal
        return await step_context.end_dialog()